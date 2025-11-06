from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from webagent.agent_service import execute_agent, AgentRequest, AgentResponse, AsyncAgentResponse
from webagent.task_repository import (
    create_task_and_task_run,
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

@app.post("/run", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
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
        return await execute_agent(request, task_id, task_run_id)
    except Exception as e:
        logger.error(f"Error while executing agent {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error while executing agent")

@app.post("/async-run", response_model=AsyncAgentResponse)
async def async_run_agent(request: AgentRequest, background_tasks: BackgroundTasks):
    try:
        result = create_task_and_task_run(
            prompt=request.task,
            model=request.model,
            provider=request.provider.value,
            webhook_url=request.webhook_url,
            json_schema=request.json_schema_str
        )
        task = result["task"]
        task_run = result["task_run"]
        
        logger.info(f"Created task ID: {task.id} and task run ID: {task_run.id}")
        
        response = AsyncAgentResponse(
            task_id=task.id,
            task_run_id=task_run.id
        )
        
        # Create a wrapper function to await the async execute_agent function
        async def execute_agent_wrapper(req, t_id, tr_id):
            await execute_agent(req, t_id, tr_id)
        
        background_tasks.add_task(execute_agent_wrapper, request, task.id, task_run.id)
        
        logger.info(f"Added task to background: {request.task}")
        return response
    except Exception as e:
        logger.error(f"Error while setting up async agent {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error while setting up async agent")
