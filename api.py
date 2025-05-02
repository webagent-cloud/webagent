from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field, SecretStr
from models import (
    ProviderEnum,
    StatusEnum,
    HistoryItem,
)
from typing import Any, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_mistralai import ChatMistralAI
from langchain_together import Together
from browser_use import Agent, Browser, BrowserConfig
from dotenv import load_dotenv
import logging
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Webagent API",
    description="API to execute automated tasks on browser using different LLM providers.",
    version="0.1.0"
)

class AgentRequest(BaseModel):
    task: str = Field(..., min_length=3, description="The task to be performed by the agent")
    model: str = "gpt-4o"
    provider: ProviderEnum = ProviderEnum.openai

class AgentResponse(BaseModel):
    """
    Represents the complete response from the agent.
    """
    history: Optional[list[HistoryItem]] = Field(None, description="List of steps in the history")
    result: Optional[Any] = Field(None, description="The final result of the agent's task")
    is_done: Optional[bool] = Field(None, description="Whether the agent has completed its task")
    is_successful: Optional[bool] = Field(None, description="Whether the agent was successful in completing its task")
    status: StatusEnum = Field(StatusEnum.in_progress, description="The status of the agent's task")
    screenshots: Optional[Any] = Field(None, description="The Base64 screenshots taken during the task")

def get_llm(provider: ProviderEnum, model: str):
    """
    Returns the appropriate LLM based on the provider and model.
    """
    if provider == ProviderEnum.openai:
        return ChatOpenAI(model=model)
    elif provider == ProviderEnum.deepseek:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        return ChatOpenAI(base_url='https://api.deepseek.com/v1', model=model, api_key=SecretStr(api_key))
    elif provider == ProviderEnum.anthropic:
        return ChatAnthropic(model_name=model)
    elif provider == ProviderEnum.google:
        return ChatGoogleGenerativeAI(model=model)
    elif provider == ProviderEnum.groq:
        return ChatGroq(model=model)
    elif provider == ProviderEnum.mistral:
        return ChatMistralAI(model=model)
    elif provider == ProviderEnum.together:
        return Together(model=model)
    else:
        return ChatOpenAI(model=model)

async def execute_agent(request: AgentRequest):
    """
    Execute the agent with the given request parameters.
    This function is used by both synchronous and asynchronous routes.
    """
    logger.info(f"Starting agent with task: {request.task}, provider: {request.provider}, model: {request.model}")
    
    llm = get_llm(request.provider, request.model)
    
    config = BrowserConfig(
        headless=True,
    )

    browser = Browser(
        config=config,
    )
    agent = Agent(
        task=request.task,
        llm=llm,
        browser=browser,
    )
    
    agent_results = await agent.run()
    final_result = agent_results.final_result()
    is_done = agent_results.is_done()
    is_successful = agent_results.is_successful()
    
    history = [
        HistoryItem(
            is_done=item.is_done,
            success=item.success,
            extracted_content=item.extracted_content,
            error=item.error,
            include_in_memory=item.include_in_memory,
        )
        for item in agent_results.action_results()
    ]
    
    screenshots = agent_results.screenshots()
    
    status = StatusEnum.in_progress
    if is_done:
        status = StatusEnum.success if is_successful else StatusEnum.failure
        
    return AgentResponse(
        history=history,
        result=final_result,
        is_done=is_done,
        is_successful=is_successful,
        status=status,
        screenshots=screenshots,
    )

@app.post("/run", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    try:
        return await execute_agent(request)
    except Exception as e:
        logger.error(f"Error while executing agent {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error while executing agent")

@app.post("/async-run", response_model=AgentResponse)
async def async_run_agent(request: AgentRequest, background_tasks: BackgroundTasks):
    try:
        response = AgentResponse(
            history=[],
            result=None,
            is_done=False,
            is_successful=None,
            status=StatusEnum.in_progress,
            screenshots=None,
        )
        
        background_tasks.add_task(execute_agent, request)
        
        logger.info(f"Added task to background: {request.task}")
        return response
    except Exception as e:
        logger.error(f"Error while setting up async agent {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error while setting up async agent")
