from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional
from webagent.agent_service import execute_agent, AgentRequest, AgentResponse, AsyncAgentResponse, TaskRunRequest
from webagent.task_repository import (
    create_task_and_task_run,
    create_task_run,
    get_all_tasks,
    get_task,
    get_task_run_with_steps,
    get_task_runs,
    update_task,
)
from webagent.models import ProviderEnum, LightTaskRun
from webagent.workflow_builder_service import build_workflow_from_run
from dotenv import load_dotenv
import logging
import os
from pathlib import Path

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Webagent API",
    description="API to execute automated tasks on browser using different LLM providers.",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create API router with /api prefix
api_router = APIRouter(prefix="/api")

@api_router.get("/tasks")
async def list_tasks():
    """Get all tasks"""
    try:
        tasks = get_all_tasks()
        return {"tasks": [task.to_dict() for task in tasks]}
    except Exception as e:
        logger.error(f"Error while fetching tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Error while fetching tasks")


@api_router.get("/tasks/{task_id}")
async def get_task_by_id(task_id: int):
    """Get a single task by ID"""
    try:
        task = get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
        return task.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error while fetching task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error while fetching task")


@api_router.get("/tasks/{task_id}/runs", response_model=list[LightTaskRun])
async def get_runs_for_task(task_id: int):
    """Get all runs for a specific task (lightweight version)"""
    try:
        # First check if the task exists
        task = get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

        # Get all runs for this task
        runs = get_task_runs(task_id)

        # Convert to lightweight format
        light_runs = [
            LightTaskRun(
                id=run.id,
                description=run.prompt,
                is_done=run.is_done,
                is_successful=run.is_successful
            )
            for run in runs
        ]

        return light_runs
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error while fetching runs for task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error while fetching runs")


class TaskUpdateRequest(BaseModel):
    """Request model for updating a task"""
    prompt: Optional[str] = Field(None, min_length=3, description="The task prompt")
    model: Optional[str] = Field(None, description="The model to use")
    provider: Optional[ProviderEnum] = Field(None, description="The provider to use")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for notifications")
    response_format: Optional[str] = Field(None, description="Response format (text or json)")
    json_schema: Optional[str] = Field(None, description="JSON schema for structured output")
    cached_workflow: Optional[dict] = Field(None, description="Cached workflow definition")
    use_cached_workflow: Optional[bool] = Field(None, description="Whether to use cached workflow")


@api_router.put("/tasks/{task_id}")
async def update_task_by_id(task_id: int, request: TaskUpdateRequest):
    """Update a task by ID"""
    try:
        # Get the existing task
        task = get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

        # Build update data from request
        update_data = {}
        if request.prompt is not None:
            update_data["prompt"] = request.prompt
        if request.model is not None:
            update_data["model"] = request.model
        if request.provider is not None:
            update_data["provider"] = request.provider.value
        if request.webhook_url is not None:
            update_data["webhook_url"] = request.webhook_url
        if request.response_format is not None:
            update_data["response_format"] = request.response_format
        if request.json_schema is not None:
            update_data["json_schema"] = request.json_schema
        if request.cached_workflow is not None:
            update_data["cached_workflow"] = request.cached_workflow
        if request.use_cached_workflow is not None:
            update_data["use_cached_workflow"] = request.use_cached_workflow

        # Update the task
        updated_task = update_task(task_id, update_data)
        if not updated_task:
            raise HTTPException(status_code=404, detail=f"Failed to update task {task_id}")

        return updated_task.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error while updating task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error while updating task: {str(e)}")


@api_router.post("/tasks/{task_id}/runs", response_model=AgentResponse | AsyncAgentResponse)
async def run_task(task_id: int, request: TaskRunRequest, background_tasks: BackgroundTasks):
    """Run an existing task with optional parameter overrides"""
    try:
        # Get the existing task
        task = get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

        # Merge task parameters with request overrides
        merged_prompt = request.prompt if request.prompt is not None else task.prompt
        merged_model = request.model if request.model is not None else task.model
        merged_provider = request.provider if request.provider is not None else ProviderEnum(task.provider)
        merged_webhook_url = request.webhook_url if request.webhook_url is not None else task.webhook_url
        merged_response_format = request.response_format if request.response_format is not None else task.response_format
        merged_json_schema = request.json_schema_str if request.json_schema is not None else task.json_schema
        merged_wait_for_completion = request.wait_for_completion if request.wait_for_completion is not None else True

        # Create a new task run with merged parameters
        task_run = create_task_run(
            task_id=task_id,
            prompt=merged_prompt,
            model=merged_model,
            provider=merged_provider.value,
            webhook_url=merged_webhook_url,
            response_format=merged_response_format,
            json_schema=merged_json_schema
        )
        task_run_id = task_run.id

        # Build AgentRequest with merged parameters
        # Only include json_schema if it's not None
        agent_request_params = {
            "prompt": merged_prompt,
            "model": merged_model,
            "provider": merged_provider,
            "wait_for_completion": merged_wait_for_completion,
            "webhook_url": merged_webhook_url,
        }

        # Add json_schema only if we have a value
        merged_json_schema_for_request = request.json_schema if request.json_schema is not None else (task.json_schema if task.json_schema else None)
        if merged_json_schema_for_request is not None:
            agent_request_params["json_schema"] = merged_json_schema_for_request

        agent_request = AgentRequest(**agent_request_params)

        # Set use_cached_workflow from request or task
        agent_request.use_cached_workflow = request.use_cached_workflow if request.use_cached_workflow is not None else task.use_cached_workflow
        agent_request.cached_workflow = task.cached_workflow

        # Validate that cached_workflow exists if use_cached_workflow is True
        if agent_request.use_cached_workflow and not agent_request.cached_workflow:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot use cached workflow: Task {task_id} does not have a cached workflow. Please create one first by calling POST /api/runs/{{run_id}}/set-as-cached-workflow"
            )

        # If wait_for_completion is False, execute in background and return immediately
        if not merged_wait_for_completion:
            logger.info(f"Running task ID: {task_id} with task run ID: {task_run_id}")

            # Create a wrapper function to await the async execute_agent function
            async def execute_agent_wrapper(req, t_id, tr_id):
                await execute_agent(req, t_id, tr_id)

            background_tasks.add_task(execute_agent_wrapper, agent_request, task_id, task_run_id)

            logger.info(f"Added task to background: {merged_prompt}")
            return AsyncAgentResponse(
                task_id=task_id,
                task_run_id=task_run_id
            )

        # Otherwise, execute synchronously and wait for result
        return await execute_agent(agent_request, task_id, task_run_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error while running task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error while running task")


@api_router.post("/runs", response_model=AgentResponse | AsyncAgentResponse)
async def run_agent(request: AgentRequest, background_tasks: BackgroundTasks):
    try:
        result = create_task_and_task_run(
            prompt=request.prompt,
            model=request.model,
            provider=request.provider.value,
            webhook_url=request.webhook_url,
            response_format=request.response_format,
            json_schema=request.json_schema_str
        )
        task_id = result["task"].id
        task_run_id = result["task_run"].id

        # If wait_for_completion is False, execute in background and return immediately
        if not request.wait_for_completion:
            logger.info(f"Created task ID: {task_id} and task run ID: {task_run_id}")

            # Create a wrapper function to await the async execute_agent function
            async def execute_agent_wrapper(req, t_id, tr_id):
                await execute_agent(req, t_id, tr_id)

            background_tasks.add_task(execute_agent_wrapper, request, task_id, task_run_id)

            logger.info(f"Added task to background: {request.prompt}")
            return AsyncAgentResponse(
                task_id=task_id,
                task_run_id=task_run_id
            )

        # Otherwise, execute synchronously and wait for result
        return await execute_agent(request, task_id, task_run_id)
    except Exception as e:
        logger.error(f"Error while executing agent {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error while executing agent")


@api_router.get("/runs/{run_id}")
async def get_run_by_id(run_id: int):
    """Get a run by ID with all details, steps, and actions"""
    try:
        # Get the task run with steps and actions eagerly loaded
        task_run_data = get_task_run_with_steps(run_id)
        if not task_run_data:
            raise HTTPException(status_code=404, detail=f"Task run with ID {run_id} not found")

        return task_run_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error while fetching run {run_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error while fetching run")


@api_router.post("/runs/{run_id}/set-as-cached-workflow")
async def set_run_as_cached_workflow(run_id: int):
    """
    Extract parameters from a run's prompt and create a templated workflow
    that can be cached in the related task.
    """
    try:
        # Get the task run with steps eagerly loaded
        task_run_data = get_task_run_with_steps(run_id)
        if not task_run_data:
            raise HTTPException(status_code=404, detail=f"Task run with ID {run_id} not found")

        # Get the related task
        task = get_task(task_run_data["task_id"])
        if not task:
            raise HTTPException(status_code=404, detail=f"Task with ID {task_run_data['task_id']} not found")

        # Build the workflow template
        logger.info(f"Building workflow from run {run_id}")

        # Steps are already in dict format from get_task_run_with_steps
        steps_data = task_run_data.get("steps", [])

        workflow_template = await build_workflow_from_run(
            task_prompt=task_run_data["prompt"],
            steps=steps_data
        )

        # Update the task with the cached workflow
        workflow_dict = workflow_template.to_dict()
        update_task(task.id, {
            "cached_workflow": workflow_dict,
            "use_cached_workflow": True
        })

        logger.info(f"Successfully cached workflow for task {task.id} from run {run_id}")

        return {
            "success": True,
            "workflow": workflow_dict,
            "message": f"Successfully extracted {len(workflow_template.parameters)} parameter(s) and created workflow template",
            "task_id": task.id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error while building workflow from run {run_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error while building workflow: {str(e)}")


# Include the API router in the app
app.include_router(api_router)

# Mount static files
# Get the path to the frontend/dist directory
static_dir = Path(__file__).parent.parent / "frontend" / "dist"

# Check if dist directory exists, if not log a warning
if static_dir.exists() and static_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
    logger.info(f"Serving static files from {static_dir}")
else:
    logger.warning(f"Static directory not found at {static_dir}. Frontend will not be served.")
