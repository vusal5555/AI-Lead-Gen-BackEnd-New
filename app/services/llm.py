import google.genai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from typing import Optional, Type
from pydantic import BaseModel

from app.config import get_settings


def get_gemini_model(model_str: str = "gemini-2.5-pro") -> ChatGoogleGenerativeAI:
    """
    Get a LangChain Gemini model instance.

    Args:
        model_name: The Gemini model to use
                   - gemini-1.5-flash: Fast, good for most tasks
                   - gemini-1.5-pro: More capable, slower
    """

    settings = get_settings()

    return ChatGoogleGenerativeAI(
        model=model_str,
        api_key=settings.gemini_api_key,
        temperature=0.1,
    )


def invoke_llm(
    system_prompt: str,
    user_message: str,
    model_name: str = "gemini-2.5-flash",
    response_format: Optional[Type[BaseModel]] = None,
):
    """
    Invoke the LLM with a system prompt and user message.

    This is the main function for all LLM calls in the application.

    Args:
        system_prompt: Instructions for the LLM
        user_message: The actual content to process
        model_name: Which Gemini model to use
        response_format: Optional Pydantic model for structured output

    Returns:
        String response or Pydantic model instance if response_format provided

    Example:
        # Simple text response
        result = invoke_llm(
            system_prompt="You are a helpful assistant.",
            user_message="Summarize this text: ..."
        )

        # Structured response
        class Summary(BaseModel):
            title: str
            key_points: list[str]

        result = invoke_llm(
            system_prompt="Extract information from this text.",
            user_message="...",
            response_format=Summary
        )
    """

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    llm = get_gemini_model(model_name)

    if response_format:
        llm = llm.with_structured_output(response_format)
    else:
        llm = llm | StrOutputParser()

    ouput = llm.invoke(messages)

    return ouput


async def invoke_llm_async(
    system_prompt: str,
    user_message: str,
    model_name: str = "gemini-2.5-flash",
    response_format: Optional[Type[BaseModel]] = None,
):
    """
    Async version of invoke_llm for use in FastAPI endpoints.
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message),
    ]

    llm = get_gemini_model(model_name)

    if response_format:
        llm = llm.with_structured_output(response_format)
    else:
        llm = llm | StrOutputParser()

    # Use ainvoke for async
    output = await llm.ainvoke(messages)

    return output
