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
from browser_use import Agent, Browser, Controller
from pydantic import BaseModel, Field, field_validator, computed_field
import logging
import json
from jsonschema import Draft7Validator, exceptions as jsonschema_exceptions
from jambo.schema_converter import SchemaConverter
from browser_providers.browser_service_selector import get_browser_service

logger = logging.getLogger(__name__)

class AgentRequest(BaseModel):
    task: str = Field(..., min_length=3, description="The task to be performed by the agent")
    model: str = "gpt-4o"
    provider: ProviderEnum = ProviderEnum.openai
    webhook_url: Optional[str] = Field(None, description="URL to send webhook notification when task is complete")
    json_schema: Optional[str | dict] = Field(None, description="The JSON schema for the task result")
    @field_validator("json_schema")
    @classmethod
    def validate_json_schema(cls, v):
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON string: {e.msg}")
        try:
            Draft7Validator.check_schema(v)
        except jsonschema_exceptions.SchemaError as e:
            raise ValueError(f"Invalid JSON Schema: {e.message}")
        return v

    @computed_field
    @property
    def json_schema_model(self) -> Any:
        if self.json_schema is None:
            return None
        schema = self.json_schema
        if isinstance(schema, str):
            try:
                schema = json.loads(schema)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON string: {e.msg}")
        if "title" not in schema:
            schema["title"] = "Model"
        return SchemaConverter.build(schema)
    
    @computed_field
    @property
    def json_schema_str(self) -> str:
        if self.json_schema is None:
            return None
        if isinstance(self.json_schema, str):
            return self.json_schema
        return json.dumps(self.json_schema, indent=2)

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
    browser_service = get_browser_service()
    session_response = await browser_service.create_session(session_timeout=900)
    
    controller = Controller(output_model=request.json_schema_model)
    browser = Browser(
        cdp_url=session_response["cdp_url"],
    )

    agent = Agent(
        task=request.task,
        llm=llm,
        browser=browser,
        controller=controller,
    )
    
    agent_results = await agent.run()

    await browser_service.close_session()

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
