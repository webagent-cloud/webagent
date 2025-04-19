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

class HistoryItem(BaseModel):
    """
    Represents an individual step in the agent's history.
    """
    is_done: Optional[bool] = Field(None, description="Whether the step is done")
    success: Optional[bool] = Field(None, description="Whether the step was successful")
    extracted_content: Optional[str] = Field(None, description="Content extracted from the step")
    error: Optional[str] = Field(None, description="Error message if any")
    include_in_memory: Optional[bool] = Field(None, description="Whether to include this step in memory")