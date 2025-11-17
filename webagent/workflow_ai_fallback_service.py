"""
Workflow AI Fallback Service - handles AI fallback when cached workflow actions fail.
Provides context-aware AI execution for failed steps with retry logic.
"""
import logging
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from webagent.models import HistoryItem, Action, ProviderEnum
from webagent.llm_service import get_llm
from webagent.engine_providers.engine_service_selector import get_engine_service

if TYPE_CHECKING:
    from webagent.agent_service import AgentRequest

logger = logging.getLogger(__name__)

# Configuration
MAX_AI_FALLBACK_RETRIES = 3
AI_FALLBACK_TIMEOUT = 30000  # milliseconds


async def execute_step_with_ai_fallback(
    session_response: Dict[str, Any],
    step: Dict[str, Any],
    failed_action: Action,
    workflow_context: List[HistoryItem],
    provider: ProviderEnum,
    model: str,
    original_task_prompt: str
) -> tuple[List[Action], bool]:
    """
    Execute a failed step using AI engine with retry logic.

    When a cached action fails, this function:
    1. Constructs a focused task for the AI with context
    2. Executes using the same engine provider (browser-use, etc.)
    3. Retries up to MAX_AI_FALLBACK_RETRIES times
    4. Returns AI-generated actions marked with execution metadata

    Args:
        session_response: Browser session response with cdp_url
        step: The workflow step that failed (contains description and actions)
        failed_action: The specific action that failed
        workflow_context: History of successfully completed steps (for context)
        provider: LLM provider to use for AI fallback
        model: Model name to use for AI fallback
        original_task_prompt: The original task prompt (for broader context)

    Returns:
        Tuple of (AI-generated actions list, success boolean)
        - actions: List of Action objects executed by AI
        - success: Whether AI successfully completed the step
    """
    step_description = step.get("description", "")

    logger.info(f"Starting AI fallback for step: {step_description}")
    logger.info(f"Failed action: {failed_action.name} with error: {failed_action.error}")

    # Construct AI task with context
    ai_task = _build_ai_task_with_context(
        step_description=step_description,
        failed_action=failed_action,
        workflow_context=workflow_context,
        original_task_prompt=original_task_prompt
    )

    logger.info(f"AI fallback task: {ai_task}")

    # Retry loop
    for attempt in range(1, MAX_AI_FALLBACK_RETRIES + 1):
        logger.info(f"AI fallback attempt {attempt}/{MAX_AI_FALLBACK_RETRIES}")

        try:
            # Get LLM and engine service
            llm = get_llm(provider, model)
            engine_service = get_engine_service()

            # Import AgentRequest only at runtime to avoid circular import
            from webagent.agent_service import AgentRequest

            # Create a minimal AgentRequest for the AI sub-task
            ai_request = AgentRequest(
                prompt=ai_task,
                model=model,
                provider=provider,
                wait_for_completion=True
            )

            # Execute the step with AI
            engine_result = await engine_service.run(
                request=ai_request,
                session_response=session_response,
                llm=llm
            )

            # Check if AI was successful
            if engine_result.is_successful:
                logger.info(f"AI fallback succeeded on attempt {attempt}")

                # Extract actions from AI execution and mark them
                ai_actions = _extract_and_mark_ai_actions(
                    history=engine_result.history,
                    failed_action=failed_action,
                    attempt=attempt
                )

                return ai_actions, True

            else:
                logger.warning(f"AI fallback attempt {attempt} completed but was not successful")
                if attempt < MAX_AI_FALLBACK_RETRIES:
                    logger.info(f"Retrying AI fallback (attempt {attempt + 1}/{MAX_AI_FALLBACK_RETRIES})")
                    continue

        except Exception as e:
            logger.error(f"AI fallback attempt {attempt} failed with exception: {str(e)}")
            if attempt < MAX_AI_FALLBACK_RETRIES:
                logger.info(f"Retrying AI fallback (attempt {attempt + 1}/{MAX_AI_FALLBACK_RETRIES})")
                continue
            else:
                logger.error(f"AI fallback exhausted all {MAX_AI_FALLBACK_RETRIES} retries")

    # All retries failed
    logger.error(f"AI fallback failed after {MAX_AI_FALLBACK_RETRIES} attempts")
    return [], False


def _build_ai_task_with_context(
    step_description: str,
    failed_action: Action,
    workflow_context: List[HistoryItem],
    original_task_prompt: str
) -> str:
    """
    Build a focused AI task with context similar to browser-use Agent.

    Includes:
    - Original high-level task
    - What has been accomplished so far (workflow_context)
    - Current step goal
    - What failed and why
    """
    # Build context from previous successful steps
    context_summary = ""
    if workflow_context:
        context_summary = "\n\nPreviously completed steps:"
        for i, history_item in enumerate(workflow_context[-3:], 1):  # Last 3 steps for context
            context_summary += f"\n{i}. {history_item.description}"
            # Include key actions if available
            if history_item.actions:
                successful_actions = [a for a in history_item.actions if a.success]
                if successful_actions:
                    action_names = [a.name for a in successful_actions[:3]]  # First 3 actions
                    context_summary += f" (actions: {', '.join(action_names)})"

    # Build the AI task - structure it to avoid re-executing the whole workflow
    # The task should be ONLY the current step, with context as background info
    ai_task = f"""{step_description}

BACKGROUND CONTEXT (for your information only - these steps are ALREADY completed):
- Original workflow task: {original_task_prompt}{context_summary}

CURRENT STATUS:
- The browser is currently in the state after completing the above steps
- The cached action '{failed_action.name}' failed with error: {failed_action.error}

YOUR TASK (complete ONLY this specific action, then mark as done):
{step_description}

Execute the minimum actions needed to complete this specific step, then immediately call the 'done' action."""

    return ai_task


def _extract_and_mark_ai_actions(
    history: List[HistoryItem],
    failed_action: Action,
    attempt: int
) -> List[Action]:
    """
    Extract actions from AI execution history and mark them as AI-executed.

    Returns flattened list of all actions from all history items,
    with metadata indicating they were executed by AI fallback.
    """
    ai_actions = []

    for history_item in history:
        if history_item.actions:
            for action in history_item.actions:
                # Mark this action as executed by AI
                action_dict = action.model_dump() if hasattr(action, 'model_dump') else action

                # Create new Action with AI metadata
                marked_action = Action(
                    name=action_dict.get('name'),
                    params=action_dict.get('params', {}),
                    is_done=action_dict.get('is_done', True),
                    success=action_dict.get('success', False),
                    extracted_content=action_dict.get('extracted_content'),
                    error=action_dict.get('error'),
                    # Add AI execution metadata
                    executed_by_ai=True,
                    fallback_reason=f"Cached action '{failed_action.name}' failed: {failed_action.error}",
                    fallback_attempt=attempt
                )

                ai_actions.append(marked_action)

    logger.info(f"Extracted {len(ai_actions)} actions from AI execution")
    return ai_actions
