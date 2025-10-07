import logging
from .engine_service import EngineService, EngineServiceResult
from typing import Any, TYPE_CHECKING
from models import HistoryItem
from browser_use import Agent, Browser, Controller

if TYPE_CHECKING:
    from agent_service import AgentRequest

logger = logging.getLogger(__name__)

class BrowseruseService(EngineService):
    async def run(self, request: "AgentRequest", session_response: dict, llm: Any) -> EngineServiceResult:
        """
        Execute the agent using browser-use with Agent, Browser, and Controller.
        """
        logger.info(f"Starting browser-use agent with task: {request.task}")
        
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
        logger.info(f"Browser-use agent completed")
        
        # Extract standard results from browser-use
        final_result = agent_results.final_result()
        is_done = agent_results.is_done()
        is_successful = agent_results.is_successful()
        
        # Build history from action results
        history = []
        for item in agent_results.action_results():
            history_item = HistoryItem(
                is_done=item.is_done,
                success=item.success,
                extracted_content=item.extracted_content,
                error=item.error,
                include_in_memory=item.include_in_memory,
            )
            history.append(history_item)
        
        screenshots = agent_results.screenshots()
        
        # Build run steps data for database storage
        run_steps = []
        for i, item in enumerate(agent_results.action_results()):
            step_data = {
                "result": item.extracted_content,
                "errors": item.error,
                "is_done": item.is_done,
                "is_successful": item.success,
                "screenshot": screenshots[i] if i < len(screenshots) else None
            }
            run_steps.append(step_data)
        
        return EngineServiceResult(
            final_result=final_result,
            is_done=is_done,
            is_successful=is_successful,
            history=history,
            screenshots=screenshots,
            run_steps=run_steps
        )
