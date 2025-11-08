from webagent.models import (
    ProviderEnum,
    StatusEnum,
    HistoryItem,
)
from webagent.llm_service import get_llm
from webagent.task_repository import (
    update_task_run,
    create_run_step,
    create_run_action,
    get_task,
    Task,
)
from webagent.webhook_service import post_webhook
from webagent.workflow_replay_service import (
    extract_parameters_from_task,
    apply_parameters_to_workflow,
    replay_workflow,
)
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator, computed_field
import logging
import json
from jsonschema import Draft7Validator, exceptions as jsonschema_exceptions
from jambo.schema_converter import SchemaConverter
from webagent.browser_providers.browser_service_selector import get_browser_service
from webagent.engine_providers.engine_service_selector import get_engine_service

logger = logging.getLogger(__name__)

class AgentRequest(BaseModel):
    prompt: str = Field(..., min_length=3, description="The task to be performed by the agent")
    model: str = "o3"
    provider: ProviderEnum = ProviderEnum.openai
    wait_for_completion: Optional[bool] = Field(
        True,
        description="Whether to wait for the task to complete before returning the response. If false, the task will be executed in the background and the response will contain only the task ID."
    )
    webhook_url: Optional[str] = Field(None, description="URL to send webhook notification when task is complete")
    response_format: Optional[str] = Field('text', description="Whether to return the result as text or JSON")
    json_schema: Optional[str | dict] = Field(None, description="The JSON schema for the task result")
    use_cached_workflow: Optional[bool] = Field(None, exclude=True, description="Internal field: whether to use cached workflow")
    cached_workflow: Optional[dict] = Field(None, exclude=True, description="Internal field: the cached workflow data")
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

class TaskRunRequest(BaseModel):
    """Request model for running an existing task with optional parameter overrides"""
    prompt: Optional[str] = Field(None, min_length=3, description="Override task prompt")
    model: Optional[str] = Field(None, description="Override model")
    provider: Optional[ProviderEnum] = Field(None, description="Override provider")
    wait_for_completion: Optional[bool] = Field(
        None,
        description="Whether to wait for the task to complete before returning the response. If false, the task will be executed in the background and the response will contain only the task ID."
    )
    webhook_url: Optional[str] = Field(None, description="Override webhook URL")
    response_format: Optional[str] = Field(None, description="Whether to return the result as text or JSON")
    json_schema: Optional[str | dict] = Field(None, description="Override JSON schema for the task result")
    use_cached_workflow: Optional[bool] = Field(None, description="Override whether to use cached workflow instead of AI")

    @field_validator("json_schema")
    @classmethod
    def validate_json_schema(cls, v):
        if v is None:
            return v
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

    If request.use_cached_workflow is True, it will replay the cached workflow instead of using AI.
    """
    logger.info(f"Starting agent with task: {request.prompt}, provider: {request.provider}, model: {request.model}")

    browser_service = get_browser_service()
    session_response = await browser_service.create_session(session_timeout=900)

    try:
        # Check if we should use cached workflow
        if request.use_cached_workflow and request.cached_workflow:
            logger.info(f"Using cached workflow for task ID: {task_id}")

            # Extract parameters from the task prompt
            parameter_values = await extract_parameters_from_task(
                task_prompt=request.prompt,
                workflow=request.cached_workflow,
                provider=request.provider,
                model=request.model
            )

            # Apply parameters to workflow
            processed_workflow = apply_parameters_to_workflow(
                workflow=request.cached_workflow,
                parameter_values=parameter_values
            )

            # Replay the workflow
            history, screenshots, final_result = await replay_workflow(
                session_response=session_response,
                workflow=processed_workflow,
                use_ai_fallback=False
            )

            is_done = True
            is_successful = True

        else:
            logger.info(f"Using AI engine for task ID: {task_id}")

            llm = get_llm(request.provider, request.model)

            # Get the appropriate engine service based on configuration
            engine_service = get_engine_service()

            # Execute the agent using the selected engine - this now returns standardized EngineServiceResult
            engine_result = await engine_service.run(
                request=request,
                session_response=session_response,
                llm=llm
            )

            # Extract standardized results from engine service
            final_result = engine_result.final_result
            is_done = engine_result.is_done
            is_successful = engine_result.is_successful
            history = engine_result.history
            screenshots = engine_result.screenshots

        # Create run steps and actions in database from history
        for i, history_item in enumerate(history):
            step_number = i + 1
            # Create the run step with description and screenshot
            step_data = {
                "description": history_item.description,
                "screenshot": screenshots[i] if i < len(screenshots) else None
            }
            create_run_step(task_run_id, step_number, step_data)

            # Create run actions for each action in the step
            if history_item.actions:
                for j, action in enumerate(history_item.actions):
                    action_number = j + 1
                    action_data = action.model_dump()
                    create_run_action(task_run_id, step_number, action_number, action_data)

        # Update task run with results
        update_task_run(task_run_id, {
            "result": final_result,
            "is_done": is_done,
            "is_successful": is_successful
        })

        logger.info(f"Updated task run ID: {task_run_id} with results")

        status = StatusEnum.in_progress
        if is_done:
            status = StatusEnum.success if is_successful else StatusEnum.failure

        response = AgentResponse(
            task_id=task_id,
            task_run_id=task_run_id,
            history=history,
            result=final_result,
            is_done=is_done,
            is_successful=is_successful,
            status=status,
        )

        # Send webhook if URL is provided
        if request.webhook_url:
            await post_webhook(
                webhook_url=request.webhook_url,
                data=response.model_dump(),
                task_run_id=task_run_id,
            )

        return response

    finally:
        # Always close the browser session
        await browser_service.close_session()
