import logging
from .engine_service import EngineService, EngineServiceResult
from typing import Any, TYPE_CHECKING
from models import HistoryItem
import notte

if TYPE_CHECKING:
    from agent_service import AgentRequest

logger = logging.getLogger(__name__)

class NotteService(EngineService):
    async def run(self, request: "AgentRequest", session_response: dict, llm: Any) -> EngineServiceResult:
        """
        Execute the agent using Notte with Session and Agent.
        """
        logger.info(f"Starting Notte agent with task: {request.task}")
        
        with notte.Session(cdp_url=session_response["cdp_url"]) as session:
            agent = notte.Agent(session=session, reasoning_model='gemini/gemini-2.5-flash', max_steps=30)
            response = agent.run(task=request.task)

            # Access the trajectory from the response  
            trajectory = response.trajectory
            # Get all execution results
            execution_results = list(trajectory.execution_results())

            # Build standardized response format
            # Extract final result
            if hasattr(response, 'answer'):
                final_result = response.answer
            elif hasattr(response, 'result'):
                final_result = response.result
            else:
                final_result = str(response)
            
            # Determine success status
            is_successful = getattr(response, 'success', True)
            is_done = True  # Notte always completes
            
            # Build history from execution results
            history = []
            for i, result in enumerate(execution_results):
                history_item = HistoryItem(
                    is_done=(i == len(execution_results) - 1),
                    success=result.success,
                    extracted_content=result.message if result.message else f"Action: {result.action.type}",
                    error=None if result.success else f"Failed action: {result.action.type}",
                    include_in_memory=True
                )
                history.append(history_item)
            
            # Build run steps data for database storage
            run_steps = []
            for i, result in enumerate(execution_results):
                step_data = {
                    "result": result.message if result.message else f"Action: {result.action.type}",
                    "errors": None if result.success else f"Failed action: {result.action.type}",
                    "is_done": True,
                    "is_successful": result.success,
                    "screenshot": None  # Notte doesn't provide screenshots in the same way
                }
                run_steps.append(step_data)
            
            # Screenshots - Notte doesn't provide screenshots in the same format
            screenshots = []
            
            return EngineServiceResult(
                final_result=final_result,
                is_done=is_done,
                is_successful=is_successful,
                history=history,
                screenshots=screenshots,
                run_steps=run_steps
            )
