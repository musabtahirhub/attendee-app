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
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    system_prompt = (
        f"You are an AI Assistant for the Employee Attendance & Leave Management System.\n"
        f"The current user interacting with you has the role: '{user_role}'.\n"
        f"You have access to tools for checking employee status, applying for leave, and approving leave requests.\n"
        f"When invoking `approve_employee_leave`, pass user_role='{user_role}'.\n"
        f"Always provide polite, concise, and accurate responses."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    ai_msg = llm_with_tools.invoke(messages)
    messages.append(ai_msg)

    if ai_msg.tool_calls:
        for tool_call in ai_msg.tool_calls:
            t_name = tool_call["name"].lower()
            selected_tool = tools_by_name.get(t_name)
            if selected_tool:
                tool_output = selected_tool.invoke(tool_call["args"])
                messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))
            else:
                messages.append(ToolMessage(content=f"Tool '{t_name}' not found", tool_call_id=tool_call["id"]))

        final_response = llm.invoke(messages)
        return str(final_response.content)

    return str(ai_msg.content)


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
    except Exception:
        logger.exception("Unexpected error during chatbot query processing")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your chatbot request.",
        )
