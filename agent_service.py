from models import (
    ProviderEnum,
    StatusEnum,
    HistoryItem,
)
from llm_service import get_llm
from task_repository import (
    update_task_run,
    create_run_step,
)
from webhook_service import post_webhook
from typing import Any, Optional
from browser_use import Agent, Browser, BrowserConfig
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class AgentRequest(BaseModel):
    task: str = Field(..., min_length=3, description="The task to be performed by the agent")
    model: str = "gpt-4o"
    provider: ProviderEnum = ProviderEnum.openai
    webhook_url: Optional[str] = Field(None, description="URL to send webhook notification when task is complete")

class AgentResponse(BaseModel):
    """
    Represents the complete response from the agent.
    """
    task_id: Optional[int] = Field(None, description="The ID of the task")
    task_run_id: Optional[int] = Field(None, description="The ID of the task run")
    history: Optional[list[HistoryItem]] = Field(None, description="List of steps in the history")
    result: Optional[Any] = Field(None, description="The final result of the agent's task")
    is_done: Optional[bool] = Field(None, description="Whether the agent has completed its task")
    is_successful: Optional[bool] = Field(None, description="Whether the agent was successful in completing its task")
    status: StatusEnum = Field(StatusEnum.in_progress, description="The status of the agent's task")
    screenshots: Optional[Any] = Field(None, description="The Base64 screenshots taken during the task")

class AsyncAgentResponse(BaseModel):
    """
    Represents the response from the async agent endpoint.
    """
    task_id: int = Field(..., description="The ID of the created task")
    task_run_id: int = Field(..., description="The ID of the created task run")

async def execute_agent(request: AgentRequest, task_id=None, task_run_id=None):
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
    
    for i, item in enumerate(agent_results.action_results()):
        step_data = {
            "result": item.extracted_content,
            "errors": item.error,
            "is_done": item.is_done,
            "is_successful": item.success,
            "screenshot": screenshots[i] if i < len(screenshots) else None
        }
        create_run_step(task_run_id, i + 1, step_data)
    
    update_task_run(task_run_id, {
        "result": final_result,
        "is_done": is_done,
        "is_successful": is_successful
    })
    
    logger.info(f"Updated task run ID: {task_run_id} with results")
    
    response = AgentResponse(
        task_id=task_id,
        task_run_id=task_run_id,
        history=history,
        result=final_result,
        is_done=is_done,
        is_successful=is_successful,
        status=status,
        screenshots=screenshots,
    )
    
    # Send webhook if URL is provided
    if request.webhook_url:
        await post_webhook(
            webhook_url=request.webhook_url,
            data=response.model_dump(),
            task_run_id=task_run_id,
        )
        
    return response
