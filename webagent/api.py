from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from webagent.agent_service import execute_agent, AgentRequest, AgentResponse, AsyncAgentResponse, TaskRunRequest
from webagent.task_repository import (
    create_task_and_task_run,
    create_task_run,
    get_all_tasks,
    get_task,
)
from webagent.models import ProviderEnum
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


@api_router.post("/tasks/{task_id}/run", response_model=AgentResponse | AsyncAgentResponse)
async def run_task(task_id: int, request: TaskRunRequest, background_tasks: BackgroundTasks):
    """Run an existing task with optional parameter overrides"""
    try:
        # Get the existing task
        task = get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

        # Merge task parameters with request overrides
        merged_prompt = request.task if request.task is not None else task.prompt
        merged_model = request.model if request.model is not None else task.model
        merged_provider = request.provider if request.provider is not None else ProviderEnum(task.provider)
        merged_webhook_url = request.webhook_url if request.webhook_url is not None else task.webhook_url
        merged_json_schema = request.json_schema_str if request.json_schema is not None else task.json_schema
        merged_wait_for_completion = request.wait_for_completion if request.wait_for_completion is not None else True

        # Create a new task run with merged parameters
        task_run = create_task_run(
            task_id=task_id,
            prompt=merged_prompt,
            model=merged_model,
            provider=merged_provider.value,
            webhook_url=merged_webhook_url,
            json_schema=merged_json_schema
        )
        task_run_id = task_run.id

        # Build AgentRequest with merged parameters
        # Only include json_schema if it's not None
        agent_request_params = {
            "task": merged_prompt,
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


@api_router.post("/run", response_model=AgentResponse | AsyncAgentResponse)
async def run_agent(request: AgentRequest, background_tasks: BackgroundTasks):
    try:
        result = create_task_and_task_run(
            prompt=request.task,
            model=request.model,
            provider=request.provider.value,
            webhook_url=request.webhook_url,
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

            logger.info(f"Added task to background: {request.task}")
            return AsyncAgentResponse(
                task_id=task_id,
                task_run_id=task_run_id
            )

        # Otherwise, execute synchronously and wait for result
        return await execute_agent(request, task_id, task_run_id)
    except Exception as e:
        logger.error(f"Error while executing agent {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error while executing agent")


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
