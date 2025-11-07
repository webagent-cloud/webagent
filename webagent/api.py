from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from webagent.agent_service import execute_agent, AgentRequest, AgentResponse, AsyncAgentResponse
from webagent.task_repository import (
    create_task_and_task_run,
    get_all_tasks,
    get_task,
)
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Webagent API",
    description="API to execute automated tasks on browser using different LLM providers.",
    version="0.1.0"
)

@app.get("/tasks")
async def list_tasks():
    """Get all tasks"""
    try:
        tasks = get_all_tasks()
        return {"tasks": [task.to_dict() for task in tasks]}
    except Exception as e:
        logger.error(f"Error while fetching tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Error while fetching tasks")


@app.get("/tasks/{task_id}")
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


@app.post("/run", response_model=AgentResponse | AsyncAgentResponse)
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
