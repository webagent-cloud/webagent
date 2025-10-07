from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING, Dict, List, Optional
from models import HistoryItem

if TYPE_CHECKING:
    from agent_service import AgentRequest


class EngineServiceResult:
    """Standardized result format from engine services"""
    def __init__(
        self,
        final_result: Any,
        is_done: bool,
        is_successful: bool,
        history: List[HistoryItem],
        screenshots: List[Any],
        run_steps: List[Dict[str, Any]]
    ):
        self.final_result = final_result
        self.is_done = is_done
        self.is_successful = is_successful
        self.history = history
        self.screenshots = screenshots
        self.run_steps = run_steps


class EngineService(ABC):
    @abstractmethod
    async def run(self, request: "AgentRequest", session_response: dict, llm: Any, task_id: int = None, task_run_id: int = None) -> EngineServiceResult:
        """
        Execute the agent with the given request parameters.
        
        Args:
            request: The agent request containing task and configuration
            session_response: Browser session response with cdp_url
            llm: The language model instance
            task_id: Optional task ID
            task_run_id: Optional task run ID
            
        Returns:
            EngineServiceResult with standardized format
        """
        pass
