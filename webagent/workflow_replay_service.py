"""
Workflow replay service - replays cached workflows without using AI by default.
Extracts parameters from task prompts and replays actions.
"""
import json
import re
from typing import Dict, Any, List
from playwright.async_api import Page, async_playwright
from webagent.models import ProviderEnum, HistoryItem, Action
from webagent.llm_service import get_llm
from langchain_core.messages import HumanMessage
import logging

logger = logging.getLogger(__name__)


async def extract_parameters_from_task(
    task_prompt: str,
    workflow: Dict[str, Any],
    provider: ProviderEnum = ProviderEnum.google,
    model: str = "gemini-2.0-flash-exp"
) -> Dict[str, str]:
    """
    Extract parameter values from a task prompt using LLM.

    Args:
        task_prompt: The new task prompt
        workflow: The cached workflow with parameters
        provider: LLM provider to use
        model: Model name

    Returns:
        Dictionary mapping parameter names to extracted values
    """
    parameters = workflow.get("parameters", [])
    if not parameters:
        return {}

    # Check if workflow contains template variables
    workflow_str = json.dumps(workflow)
    template_var_pattern = r'\{\{\s*(\w+)\s*\}\}'
    template_vars = set(re.findall(template_var_pattern, workflow_str))

    if not template_vars:
        logger.info("No template variables found in workflow")
        return {}

    logger.info(f"Found {len(template_vars)} template variables: {template_vars}")

    # Build extraction prompt
    param_names = [p["name"] for p in parameters]
    extraction_prompt = f"""You are a workflow automation expert. Extract the parameter values from this task instruction.

Task: "{task_prompt}"

Template variables to extract: {', '.join(param_names)}

Analyze the task and provide the values for each template variable. Return ONLY a valid JSON object with this structure:
{{
  "parameterValues": {{
    "parameterName": "extracted value from the task"
  }}
}}

Example:
If task is "Search for laptop on Google" and template variable is "searchQuery", return:
{{
  "parameterValues": {{
    "searchQuery": "laptop"
  }}
}}"""

    # Get LLM and generate extraction
    llm = get_llm(provider, model)
    messages = [HumanMessage(content=extraction_prompt)]
    response = await llm.chat.ainvoke(messages)

    # Parse JSON from response
    extraction_text = response.content if hasattr(response, 'content') else str(response)

    try:
        # Try to extract from markdown code block
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', extraction_text)
        if not json_match:
            json_match = re.search(r'```\s*([\s\S]*?)\s*```', extraction_text)

        if json_match:
            json_str = json_match.group(1).strip()
        else:
            json_str = extraction_text.strip()

        data = json.loads(json_str)
        parameter_values = data.get("parameterValues", {})

        logger.info(f"Extracted parameter values: {parameter_values}")
        return parameter_values

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse parameter extraction: {extraction_text}")
        raise ValueError(f"Failed to extract parameters from task: {str(e)}")


def apply_parameters_to_workflow(
    workflow: Dict[str, Any],
    parameter_values: Dict[str, str]
) -> Dict[str, Any]:
    """
    Replace template variables in workflow with actual parameter values.

    Args:
        workflow: The cached workflow with template variables
        parameter_values: Dictionary mapping parameter names to values

    Returns:
        Workflow with template variables replaced
    """
    # Deep clone workflow
    processed_workflow = json.loads(json.dumps(workflow))

    # Replace template variables with actual values
    workflow_json = json.dumps(processed_workflow)

    for param_name, param_value in parameter_values.items():
        template_var = f"{{{{ {param_name} }}}}"
        # Escape special regex characters in the value
        escaped_template = re.escape(template_var)
        workflow_json = re.sub(escaped_template, param_value, workflow_json)

    return json.loads(workflow_json)


async def replay_workflow(
    session_response: Dict[str, Any],
    workflow: Dict[str, Any],
    use_ai_fallback: bool = True
) -> tuple[List[HistoryItem], List[str], str]:
    """
    Replay a workflow by executing its actions without AI.

    Args:
        session_response: Browser session response with cdp_url
        workflow: The workflow to replay (with parameters already applied)
        use_ai_fallback: Whether to use AI if action fails

    Returns:
        Tuple of (history, screenshots, final_result)
    """
    history: List[HistoryItem] = []
    screenshots: List[str] = []
    steps = workflow.get("steps", [])

    logger.info(f"Replaying workflow with {len(steps)} steps")

    # Connect to browser using CDP URL
    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp(session_response["cdp_url"])

    # Get the first context and page, or create them
    contexts = browser.contexts
    if contexts:
        context = contexts[0]
        pages = context.pages
        page = pages[0] if pages else await context.new_page()
    else:
        context = await browser.new_context()
        page = await context.new_page()

    for step in steps:
        step_description = step.get("description", "")
        step_actions: List[Action] = []

        logger.info(f"Executing step: {step_description}")

        actions = step.get("actions", [])
        for action_data in actions:
            action_name = action_data.get("name", "")
            action_params = action_data.get("params", {})

            logger.info(f"Executing action: {action_name} with params: {action_params}")

            try:
                # Execute action based on name
                await execute_action(page, action_name, action_params)

                # Create action record
                step_actions.append(Action(
                    name=action_name,
                    params=action_params,
                    is_done=True,
                    success=True
                ))

                # Small delay for stability
                await page.wait_for_timeout(500)

            except Exception as e:
                logger.error(f"Error executing action {action_name}: {str(e)}")

                # Record failed action
                step_actions.append(Action(
                    name=action_name,
                    params=action_params,
                    is_done=True,
                    success=False,
                    error=str(e)
                ))

                if not use_ai_fallback:
                    raise

        # Take screenshot after step
        screenshot_bytes = await page.screenshot(full_page=False)
        screenshot_base64 = screenshot_bytes.hex() if screenshot_bytes else None
        screenshots.append(screenshot_base64)

        # Create history item
        history.append(HistoryItem(
            description=step_description,
            actions=step_actions
        ))

    # Get final result (page content or URL)
    final_result = await page.evaluate("document.body.innerText") or page.url

    logger.info("Workflow replay completed")

    return history, screenshots, final_result


async def execute_action(page: Page, action_name: str, params: Dict[str, Any]):
    """
    Execute a single browser action using Playwright.

    Maps browser-use action names to Playwright operations.
    """
    # Navigation & Browser Control
    if action_name == "search":
        query = params.get("query", "")
        engine = params.get("engine", "duckduckgo")

        if engine == "google":
            await page.goto(f"https://www.google.com/search?q={query}")
        elif engine == "bing":
            await page.goto(f"https://www.bing.com/search?q={query}")
        else:  # duckduckgo
            await page.goto(f"https://duckduckgo.com/?q={query}")

        await page.wait_for_load_state("networkidle", timeout=30000)

    elif action_name == "navigate":
        url = params.get("url")
        new_tab = params.get("new_tab", False)

        if new_tab:
            # For new tab, would need context management
            logger.warning("New tab navigation not implemented in replay, opening in current tab")

        if url:
            await page.goto(url, wait_until="networkidle", timeout=30000)

    elif action_name == "go_back":
        await page.go_back(wait_until="networkidle", timeout=30000)

    elif action_name == "wait":
        seconds = params.get("seconds", 1.0)
        await page.wait_for_timeout(int(seconds * 1000))

    # Page Interaction
    elif action_name == "click":
        index = params.get("index")
        xpath = params.get("xpath")

        if xpath:
            # Use xpath if available
            await page.click(f"xpath={xpath}")
        elif index is not None:
            # Use index - would need browser state to resolve
            # For now, try common selector patterns
            logger.warning(f"Click by index {index} - xpath not available, may fail")
            # Try to find element by index in the page
            selector = f"[data-index='{index}']"
            await page.click(selector)

    elif action_name == "input":
        index = params.get("index")
        text = params.get("text", "")
        clear = params.get("clear", True)
        xpath = params.get("xpath")

        if xpath:
            if clear:
                await page.fill(f"xpath={xpath}", text)
            else:
                # If not clearing, focus and type
                await page.focus(f"xpath={xpath}")
                await page.keyboard.type(text)
        elif index is not None:
            logger.warning(f"Input by index {index} - xpath not available, may fail")
            selector = f"[data-index='{index}']"
            if clear:
                await page.fill(selector, text)
            else:
                await page.focus(selector)
                await page.keyboard.type(text)

    elif action_name == "upload_file":
        index = params.get("index")
        path = params.get("path")
        xpath = params.get("xpath")

        if xpath and path:
            await page.set_input_files(f"xpath={xpath}", path)
        elif index is not None and path:
            logger.warning(f"Upload file by index {index} - xpath not available, may fail")
            selector = f"[data-index='{index}']"
            await page.set_input_files(selector, path)

    elif action_name == "scroll":
        down = params.get("down", True)
        pages_count = params.get("pages", 1.0)
        index = params.get("index")

        if index is not None:
            # Scroll within specific element
            logger.warning("Scroll within element not fully implemented")

        if down:
            await page.evaluate(f"window.scrollBy(0, window.innerHeight * {pages_count})")
        else:
            await page.evaluate(f"window.scrollBy(0, -window.innerHeight * {pages_count})")

    elif action_name == "find_text":
        text = params.get("text", "")
        # Scroll to text
        await page.evaluate(f"""
            const element = Array.from(document.querySelectorAll('*')).find(el =>
                el.textContent.includes('{text}')
            );
            if (element) element.scrollIntoView({{behavior: 'smooth', block: 'center'}});
        """)

    elif action_name == "send_keys":
        keys = params.get("keys", "")
        await page.keyboard.press(keys)

    # JavaScript Execution
    elif action_name == "evaluate":
        code = params.get("code", "")
        if code:
            await page.evaluate(code)

    # Tab Management
    elif action_name == "switch":
        tab_id = params.get("tab_id")
        logger.warning(f"Tab switching to {tab_id} not implemented in replay")

    elif action_name == "close":
        tab_id = params.get("tab_id")
        logger.warning(f"Tab closing {tab_id} not implemented in replay")

    # Form Controls
    elif action_name == "dropdown_options":
        # Read-only action, skip
        logger.info("Skipping dropdown_options (read-only)")

    elif action_name == "select_dropdown":
        index = params.get("index")
        text = params.get("text", "")
        xpath = params.get("xpath")

        if xpath:
            await page.select_option(f"xpath={xpath}", label=text)
        elif index is not None:
            logger.warning(f"Select dropdown by index {index} - xpath not available, may fail")
            selector = f"[data-index='{index}']"
            await page.select_option(selector, label=text)

    # Content Extraction
    elif action_name == "extract":
        # Read-only action using LLM, skip in replay
        logger.info("Skipping extract action (requires LLM)")

    # Visual Analysis
    elif action_name == "screenshot":
        # Screenshot is taken after each step anyway
        logger.info("Screenshot action - captured at step end")

    # File Operations
    elif action_name == "write_file":
        # File operations would be on the local system
        logger.warning("File operations not implemented in replay")

    elif action_name == "read_file":
        logger.warning("File operations not implemented in replay")

    elif action_name == "replace_file":
        logger.warning("File operations not implemented in replay")

    # Task Completion
    elif action_name == "done":
        # Task completion action, just log it
        text = params.get("text", "")
        success = params.get("success", True)
        logger.info(f"Task done: {text}, success: {success}")

    else:
        logger.warning(f"Unknown action: {action_name}, skipping")
