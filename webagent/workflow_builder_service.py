import json
import re
from typing import Dict, Any, List
from webagent.models import ProviderEnum
from webagent.llm_service import get_llm
from langchain_core.messages import HumanMessage


class ParameterDefinition:
    def __init__(self, name: str, description: str, type: str, example_value: str):
        self.name = name
        self.description = description
        self.type = type
        self.example_value = example_value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "exampleValue": self.example_value
        }


class WorkflowTemplate:
    def __init__(self, parameters: List[ParameterDefinition], templated_steps: List[Dict[str, Any]]):
        self.parameters = parameters
        self.templated_steps = templated_steps

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parameters": [p.to_dict() for p in self.parameters],
            "steps": self.templated_steps
        }


async def build_workflow_from_run(
    task_prompt: str,
    steps: List[Dict[str, Any]],
    provider: ProviderEnum = ProviderEnum.google,
    model: str = "gemini-2.0-flash-exp"
) -> WorkflowTemplate:
    """
    Build a workflow template from a task run by extracting parameters
    and creating templated actions.

    Args:
        task_prompt: The original task prompt
        steps: List of run steps with their actions
        provider: LLM provider to use (default: google)
        model: Model name (default: gemini-2.0-flash-exp)

    Returns:
        WorkflowTemplate with parameters and templated steps
    """

    # Step 1: Extract parameters from the task using LLM
    extraction_prompt = f"""You are a workflow automation expert. Analyze the following task to identify dynamic parameters that could be replaced with variables for workflow reusability.

Task: "{task_prompt}"

Identify all dynamic values that should be extracted as parameters from the task only. For each parameter:
1. Give it a descriptive name in camelCase (e.g., searchQuery, emailAddress, userName)
2. Describe what it represents
3. Specify its type (string, number, boolean, url)
4. Provide the example value from the current execution

Focus on:
- Text input values (fill, type methods)
- URLs that might change
- Search queries
- Form field values
- Any user-specific data

Return ONLY a valid JSON object with this structure:
{{
  "parameters": [
    {{
      "name": "parameterName",
      "description": "What this parameter represents",
      "type": "string|number|boolean|url",
      "exampleValue": "the actual value from the actions"
    }}
  ]
}}

If no parameters are found, return: {{"parameters": []}}"""

    # Get LLM and generate extraction
    llm = get_llm(provider, model)
    messages = [HumanMessage(content=extraction_prompt)]
    response = await llm.ainvoke(messages)

    # Parse JSON from response (handle markdown code blocks)
    # Handle different response formats from different LLM providers
    if hasattr(response, 'completion'):
        extraction_text = response.completion
    elif hasattr(response, 'content'):
        extraction_text = response.content
    else:
        extraction_text = str(response)
    parameters_data = _parse_json_response(extraction_text)

    # Convert to ParameterDefinition objects
    parameters: List[ParameterDefinition] = []
    for param_dict in parameters_data.get("parameters", []):
        parameters.append(ParameterDefinition(
            name=param_dict["name"],
            description=param_dict["description"],
            type=param_dict["type"],
            example_value=param_dict["exampleValue"]
        ))

    # Step 2: Create templated steps by replacing values with template variables
    templated_steps = json.loads(json.dumps(steps))  # Deep clone

    # Clean up steps - remove task_run_id, screenshot, and other runtime-specific fields
    for step in templated_steps:
        # Remove fields that shouldn't be in the workflow template
        step.pop("task_run_id", None)
        step.pop("screenshot", None)

        # Clean up actions - remove id, task_run_id
        if step.get("actions"):
            for action in step["actions"]:
                action.pop("id", None)
                action.pop("task_run_id", None)

    # Apply parameter templating
    for param in parameters:
        template_var = f"{{{{ {param.name} }}}}"
        value_to_replace = str(param.example_value)

        # Replace in all steps and actions
        for step in templated_steps:
            # Replace in step description
            if step.get("description") and value_to_replace:
                step["description"] = _safe_replace(step["description"], value_to_replace, template_var)

            # Replace in actions
            if step.get("actions"):
                for action in step["actions"]:
                    # Replace in action name
                    if action.get("name") and value_to_replace:
                        action["name"] = _safe_replace(action["name"], value_to_replace, template_var)

                    # Replace in params (JSON object)
                    if action.get("params"):
                        action["params"] = _replace_in_dict(action["params"], value_to_replace, template_var)

                    # Replace in extracted_content
                    if action.get("extracted_content") and value_to_replace:
                        action["extracted_content"] = _safe_replace(
                            action["extracted_content"],
                            value_to_replace,
                            template_var
                        )

    return WorkflowTemplate(parameters, templated_steps)


def _parse_json_response(text: str) -> Dict[str, Any]:
    """Parse JSON from LLM response, handling markdown code blocks."""
    try:
        # Try to extract from markdown code block
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if not json_match:
            json_match = re.search(r'```\s*([\s\S]*?)\s*```', text)

        if json_match:
            json_str = json_match.group(1).strip()
        else:
            json_str = text.strip()

        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from LLM response: {str(e)}\nResponse: {text}")


def _safe_replace(text: str, old_value: str, new_value: str) -> str:
    """Safely replace a value in text, escaping regex special characters."""
    if not old_value:
        return text
    escaped_old = re.escape(old_value)
    return re.sub(escaped_old, new_value, text)


def _replace_in_dict(obj: Any, old_value: str, new_value: str) -> Any:
    """Recursively replace values in a dictionary or list."""
    if isinstance(obj, dict):
        return {k: _replace_in_dict(v, old_value, new_value) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_replace_in_dict(item, old_value, new_value) for item in obj]
    elif isinstance(obj, str) and obj == old_value:
        return new_value
    else:
        return obj
