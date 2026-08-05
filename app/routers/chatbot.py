import os
import time
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.chatbot_tools import (
    check_employee_status,
    apply_employee_leave,
    approve_employee_leave,
)
from app.prompts import get_system_prompt
from app.schemas import ChatRequest, ChatResponse
from app.logger import get_logger

load_dotenv()

logger = get_logger(__name__)
router = APIRouter()

# 12-Factor App: Externalized Configuration via Environment Variables
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0"))
MODEL_MAX_RETRIES = int(os.getenv("MODEL_MAX_RETRIES", "0"))
PROMPT_VERSION = os.getenv("PROMPT_VERSION", "v1.0.0")

tools = [check_employee_status, apply_employee_leave, approve_employee_leave]
tools_by_name = {t.name.lower(): t for t in tools}


def run_chatbot_agent(user_message: str, user_role: str) -> str:
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

        ai_msg = llm_with_tools.invoke(messages)

        if ai_msg.tool_calls:
            executed_results = []
            for tool_call in ai_msg.tool_calls:
                t_name = tool_call["name"].lower()
                selected_tool = tools_by_name.get(t_name)
                if selected_tool:
                    tool_output = str(selected_tool.invoke(tool_call["args"]))
                    executed_results.append(tool_output)
                else:
                    executed_results.append(f"Tool '{t_name}' not found.")

            if executed_results:
                return "\n".join(executed_results)

        return str(ai_msg.content)

    except Exception as e:
        logger.exception("Error executing chatbot agent with model '%s': %s", MODEL_NAME, str(e))
        raise


@router.post(
    "/query",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Query the AI Chatbot",
)
def chatbot_query(payload: ChatRequest):
    try:
        reply = run_chatbot_agent(payload.message, payload.user_role)
        return ChatResponse(response=reply)
    except HTTPException:
        raise
    except SQLAlchemyError:
        logger.exception("Database error during chatbot query processing")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A database error occurred while processing your chatbot request. Please try again later.",
        )
    except Exception as e:
        logger.exception("Unexpected error during chatbot query processing: %s", str(e))
        err_msg = str(e)
        if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
            detail_msg = "Rate limit / quota exceeded on the Gemini API free tier. Please wait 10-15 seconds and try your request again."
        elif "API_KEY" in err_msg.upper() or "INVALID" in err_msg.upper() or "AUTHENTICATION" in err_msg.upper():
            detail_msg = "Invalid Gemini API Key in .env. Please add a valid GOOGLE_API_KEY from https://aistudio.google.com/."
        else:
            detail_msg = f"Chatbot error: {err_msg}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail_msg,
        )
