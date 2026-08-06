import os
import time
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.chatbot_tools import (
    check_employee_status,
    apply_employee_leave,
    approve_employee_leave,
    list_pending_leaves,
    check_my_leave_requests,
)
from app.prompts import get_system_prompt
from app.schemas import ChatRequest, ChatResponse
from app.logger import get_logger

load_dotenv()

logger = get_logger(__name__)
router = APIRouter()

MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0"))
MODEL_MAX_RETRIES = int(os.getenv("MODEL_MAX_RETRIES", "0"))
PROMPT_VERSION = os.getenv("PROMPT_VERSION", "v1.0.0")

tools = [
    check_employee_status,
    apply_employee_leave,
    approve_employee_leave,
    list_pending_leaves,
    check_my_leave_requests,
]
tools_by_name = {t.name.lower(): t for t in tools}


def _clean_response_content(content) -> str:
    if not content:
        return "I'm sorry, I couldn't process your request. Please try asking in a different way."

    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict):
                if item.get("type") == "text" and "text" in item:
                    text_parts.append(item["text"])
                elif "text" in item:
                    text_parts.append(str(item["text"]))
        text = "\n".join(text_parts) if text_parts else str(content)
    else:
        text = str(content)

    text = text.strip()
    return text


def _extract_chunk_text(content) -> str:
    """Extract string text from streaming chunk content."""
    if not content:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "".join(parts)
    return str(content)


def generate_chat_stream(user_message: str, user_role: str):
    """
    Generator function that streams AI responses token-by-token using LangChain.
    Intercepts tool calls, executes them locally, and yields formatted database results.
    """
    system_prompt = get_system_prompt(version=PROMPT_VERSION, user_role=user_role)

    try:
        llm = ChatGoogleGenerativeAI(
            model=MODEL_NAME,
            temperature=MODEL_TEMPERATURE,
            max_retries=MODEL_MAX_RETRIES,
        )
        llm_with_tools = llm.bind_tools(tools)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]

        accumulated_chunk = None
        tool_calls_detected = []
        has_yielded_text = False

        for chunk in llm_with_tools.stream(messages):
            if accumulated_chunk is None:
                accumulated_chunk = chunk
            else:
                accumulated_chunk = accumulated_chunk + chunk

            # Inspect chunk for tool call triggers
            if hasattr(chunk, "tool_calls") and chunk.tool_calls:
                for tc in chunk.tool_calls:
                    if tc not in tool_calls_detected:
                        tool_calls_detected.append(tc)

            # Inspect chunk for tool call chunks
            if hasattr(chunk, "tool_call_chunks") and chunk.tool_call_chunks:
                for tc_chunk in chunk.tool_call_chunks:
                    if isinstance(tc_chunk, dict) and tc_chunk.get("name"):
                        t_name = tc_chunk["name"].lower()
                        if not any(t.get("name", "").lower() == t_name for t in tool_calls_detected):
                            tool_calls_detected.append(tc_chunk)

            # Extract text token
            text_token = _extract_chunk_text(chunk.content)

            # Yield token live if no tool calls are being processed
            if text_token and not tool_calls_detected:
                has_yielded_text = True
                yield text_token

        # Check accumulated chunk for any tool calls assembled at the end of streaming
        if accumulated_chunk and hasattr(accumulated_chunk, "tool_calls") and accumulated_chunk.tool_calls:
            for tc in accumulated_chunk.tool_calls:
                if tc not in tool_calls_detected:
                    tool_calls_detected.append(tc)

        # Tool Execution Handling (Direct Return)
        if tool_calls_detected:
            executed_results = []
            for tool_call in tool_calls_detected:
                t_name = tool_call.get("name", "").lower()
                selected_tool = tools_by_name.get(t_name)
                if selected_tool:
                    tool_args = tool_call.get("args", {})
                    logger.info("Executing tool '%s' with args: %s", t_name, tool_args)
                    tool_output = str(selected_tool.invoke(tool_args))
                    executed_results.append(tool_output)
                else:
                    executed_results.append(f"Tool '{t_name}' not found.")

            if executed_results:
                yield "\n".join(executed_results)
        elif not has_yielded_text:
            cleaned = _clean_response_content(accumulated_chunk.content if accumulated_chunk else None)
            if cleaned:
                yield cleaned

    except SQLAlchemyError as e:
        logger.exception("Database error during chatbot stream processing: %s", str(e))
        yield "Error: A database error occurred while processing your request. Please try again later."
    except Exception as e:
        logger.exception("Unexpected error during chatbot stream processing: %s", str(e))
        err_msg = str(e)
        if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
            yield "Error: Rate limit / quota exceeded on the Gemini API free tier. Please wait 10-15 seconds and try your request again."
        elif "API_KEY" in err_msg.upper() or "INVALID" in err_msg.upper() or "AUTHENTICATION" in err_msg.upper():
            yield "Error: Invalid Gemini API Key in .env. Please add a valid GOOGLE_API_KEY from https://aistudio.google.com/."
        else:
            yield f"Error: Chatbot error: {err_msg}"


def run_chatbot_agent(user_message: str, user_role: str) -> str:
    """Helper function for non-streaming query execution."""
    tokens = list(generate_chat_stream(user_message, user_role))
    return "".join(tokens)


@router.post(
    "/query",
    status_code=status.HTTP_200_OK,
    summary="Query the AI Chatbot (Streaming Response)",
)
@router.post(
    "/query-stream",
    status_code=status.HTTP_200_OK,
    summary="Query the AI Chatbot (Streaming Response)",
)
def chatbot_query(payload: ChatRequest):
    return StreamingResponse(
        generate_chat_stream(payload.message, payload.user_role),
        media_type="text/event-stream",
    )

