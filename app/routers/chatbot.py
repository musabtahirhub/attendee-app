import time
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from app.chatbot_tools import (
    check_employee_status,
    apply_employee_leave,
    approve_employee_leave,
)
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., description="User query for the chatbot")
    user_role: str = Field(default="employee", description="User role, e.g., 'employee', 'manager', or 'admin'")


class ChatResponse(BaseModel):
    response: str


tools = [check_employee_status, apply_employee_leave, approve_employee_leave]
tools_by_name = {t.name.lower(): t for t in tools}


def run_chatbot_agent(user_message: str, user_role: str) -> str:
    system_prompt = (
        f"You are an AI Assistant for the Employee Attendance & Leave Management System.\n"
        f"The current user interacting with you has the role: '{user_role}'.\n"
        f"You have access to tools for checking employee status (by ID or Name), applying for leave, and approving leave requests.\n"
        f"When invoking `check_employee_status`, pass the employee ID (e.g. '1') or Name.\n"
        f"When invoking `approve_employee_leave`, pass user_role='{user_role}'.\n"
        f"Always provide polite, concise, and accurate responses."
    )

    # Use valid fast models in order of speed and reliability
    models_to_try = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.0-flash-lite"]

    last_exception = None

    for model_name in models_to_try:
        try:
            llm = ChatGoogleGenerativeAI(model=model_name, temperature=0, max_retries=0)
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
            err_str = str(e)
            logger.warning("Model '%s' failed: %s", model_name, err_str)
            last_exception = e
            if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                time.sleep(0.5)  # Brief delay only on rate limits before trying next model
            continue

    if last_exception:
        raise last_exception
    raise RuntimeError("No LLM model succeeded.")



@router.post(
    "/query",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Query the AI Chatbot",
)
def chatbot_query(payload: ChatRequest):
    logger.info("POST /api/chatbot/query — role='%s', message='%s'", payload.user_role, payload.message)
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
