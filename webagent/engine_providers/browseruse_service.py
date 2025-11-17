import logging
from .engine_service import EngineService, EngineServiceResult
from typing import Any, TYPE_CHECKING
from webagent.models import HistoryItem
from browser_use import Agent, Browser, Controller

if TYPE_CHECKING:
    from webagent.agent_service import AgentRequest

logger = logging.getLogger(__name__)

def extract_history(history):
    """Extract action name, description, and interacted element for each action"""
    final_history = []

    # Get all action results as a flat list
    action_results_list = list(history.action_results())
    action_result_index = 0

    for history_item in history.history:
        action_details = []

        if history_item.model_output:
            # Get interacted elements for this step
            interacted_elements = history_item.state.interacted_element or [None] * len(history_item.model_output.action)

            # Iterate through each action in this step
            for action, interacted_element in zip(history_item.model_output.action, interacted_elements):
                # Get action name (the key in the action dict)
                action_dict = action.model_dump(exclude_none=True)
                action_name = list(action_dict.keys())[0] if action_dict else 'unknown'

                action_params = action_dict.get(action_name, {})

                # Remove index parameter if present
                if 'index' in action_params:
                    del action_params['index']

                # Only add xpath if interacted element exists
                if interacted_element:
                    action_params['xpath'] = interacted_element.x_path

                # Get the corresponding action result
                action_result = action_results_list[action_result_index] if action_result_index < len(action_results_list) else None

                # Store the action with its results
                action_details.append({
                    'name': action_name,
                    'params': action_params,
                    'is_done': action_result.is_done if action_result else None,
                    'success': action_result.success if action_result else None,
                    'extracted_content': action_result.extracted_content if action_result else None,
                    'error': action_result.error if action_result else None,
                    'include_in_memory': action_result.include_in_memory if action_result else None,
                })

                action_result_index += 1

        # Create history item with actions containing their results
        history_item_obj = HistoryItem(
            description=history_item.model_output.next_goal if history_item.model_output else None,
            actions=action_details
        )
        final_history.append(history_item_obj)

    return final_history

class BrowseruseService(EngineService):
    async def run(self, request: "AgentRequest", session_response: dict, llm: Any) -> EngineServiceResult:
        """
        Execute the agent using browser-use with Agent, Browser, and Controller.
        """
        logger.info(f"Starting browser-use agent with task: {request.prompt}")

        controller = Controller(output_model=request.json_schema_model)
        browser = Browser(
            cdp_url=session_response["cdp_url"],
        )

        agent = Agent(
            task=request.prompt,
            llm=llm,
            browser=browser,
            controller=controller,
        )

        agent_results = await agent.run()
        logger.info(f"Browser-use agent completed")
        ## log everything under agent_results
        logger.info(f"Agent raw: {agent_results.history}")

        # Extract standard results from browser-use
        final_result = agent_results.final_result()
        is_done = agent_results.is_done()
        is_successful = agent_results.is_successful()

        # Build history from action results
        history = extract_history(agent_results)

        screenshots = agent_results.screenshots()

        return EngineServiceResult(
            final_result=final_result,
            is_done=is_done,
            is_successful=is_successful,
            history=history,
            screenshots=screenshots
        )
