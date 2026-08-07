import os
import time
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

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


async def generate_chat_stream(user_message: str, user_role: str):
    
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

        # first pass , gathers parameters 
        ai_message_chunk = None
        async for chunk in llm_with_tools.astream(messages):
            if ai_message_chunk is None:
                ai_message_chunk = chunk
            else:
                ai_message_chunk += chunk

            # stream direct text response chunks if no tool calls 
            text_token = _extract_chunk_text(chunk.content)
            if text_token and not chunk.tool_calls:
                yield f"data: {text_token}\n\n"

        # check if model requested any tool 
        if ai_message_chunk and ai_message_chunk.tool_calls:
            messages.append(ai_message_chunk)

            for tool_call in ai_message_chunk.tool_calls:
                t_name = tool_call.get("name", "").lower()
                selected_tool = tools_by_name.get(t_name)
                
                if selected_tool:
                    tool_args = tool_call.get("args", {})
                    logger.info("Executing tool '%s' with args: %s", t_name, tool_args)
                    
                    # execute tool asynchronously if available, fallback to sync invoke
                    if hasattr(selected_tool, "ainvoke"):
                        tool_output = await selected_tool.ainvoke(tool_args)
                    else:
                        tool_output = selected_tool.invoke(tool_args)

                    messages.append(
                        ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"])
                    )
                else:
                    messages.append(
                        ToolMessage(content=f"Tool '{t_name}' not found.", tool_call_id=tool_call["id"])
                    )

            # second pass , final synthesis , feed tool results back to llm to prepare a response 
            async for chunk in llm_with_tools.astream(messages):
                text_token = _extract_chunk_text(chunk.content)
                if text_token:
                    yield f"data: {text_token}\n\n"

    except SQLAlchemyError as e:
        logger.exception("Database error during chatbot stream processing: %s", str(e))
        yield "data: Error: A database error occurred while processing your request.\n\n"
    except Exception as e:
        logger.exception("Unexpected error during chatbot stream processing: %s", str(e))
        err_msg = str(e)
        if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
            yield "data: Error: Rate limit / quota exceeded on the Gemini API free tier.\n\n"
        elif any(k in err_msg.upper() for k in ["API_KEY", "INVALID", "AUTHENTICATION"]):
            yield "data: Error: Invalid Gemini API Key in .env.\n\n"
        else:
            yield f"data: Error: Chatbot error: {err_msg}\n\n"

@router.post(
    "/query",
    status_code=status.HTTP_200_OK,
    summary="Query the AI Chatbot (Streaming Response)",
)
def chatbot_query(payload: ChatRequest):
    return StreamingResponse(
        generate_chat_stream(payload.message, payload.user_role),
        media_type="text/event-stream",
    )

