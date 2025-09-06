from pydantic import BaseModel, Field

class SessionResponse(BaseModel):
    """
    Represents a browsing session
    """
    id: str = Field(None, description="Id of the session")
    cdp_url: str = Field(None, description="The CDP url to connect to the session")
    debug_url: str = Field(None, description="The url for interactive viewer")

class BrowserService():
    async def create_session(self) -> SessionResponse:
        pass
    async def close_session(self):
        pass