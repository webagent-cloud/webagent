from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class ProviderEnum(str, Enum):
    openai = "openai"
    deepseek = "deepseek"
    anthropic = "anthropic"
    google = "google"
    groq = "groq"
    mistral = "mistral"
    together = "together"

class StatusEnum(str, Enum):
    success = "success"
    failure = "failure"
    in_progress = "in_progress"

class Action(BaseModel):
    """
    Represents an action
    """
    name: str = Field(..., description="Name of the action")
    params: Optional[dict] = Field(None, description="Parameters for the action")
    is_done: Optional[bool] = Field(None, description="Whether the action is done")
    success: Optional[bool] = Field(None, description="Whether the action was successful")
    extracted_content: Optional[str] = Field(None, description="Content extracted from the action")
    error: Optional[str] = Field(None, description="Error message if any")
    include_in_memory: Optional[bool] = Field(None, description="Whether to include this action in memory")
    executed_by_ai: Optional[bool] = Field(False, description="Whether this action was executed by AI fallback")
    fallback_reason: Optional[str] = Field(None, description="Reason why AI fallback was triggered")
    fallback_attempt: Optional[int] = Field(None, description="Which retry attempt succeeded (1-based)")

class HistoryItem(BaseModel):
    """
    Represents an individual step in the agent's history.
    """
    description: Optional[str] = Field(None, description="Description of the step")
    actions: Optional[list[Action]] = Field(None, description="List of actions taken in this step")

class LightTaskRun(BaseModel):
    """
    Lightweight representation of a task run
    """
    id: int = Field(..., description="Task run ID")
    description: str = Field(..., description="Task run description (prompt)")
    is_done: bool = Field(..., description="Whether the task run is completed")
    is_successful: Optional[bool] = Field(None, description="Whether the task run was successful")