import logging
from steel import Steel
from pydantic import BaseModel, Field
from .browser_service import BrowserService
import os

logger = logging.getLogger(__name__)

client = Steel(steel_api_key=os.environ["STEEL_API_KEY"])

class SessionResponse(BaseModel):
    """
    Represents a browsing session
    """
    id: str = Field(None, description="Id of the session")
    debug_url: str = Field(None, description="The url for interactive viewer")

def create_steel_session(session_timeout=900) -> SessionResponse:
    logger.info("Creating Steel session...")
    params = {
        'solve_captcha':True
    }

    if session_timeout:
        params['api_timeout'] = session_timeout * 1000

    return client.sessions.create(**params)

def release_steel_session(session_id):
    logger.info("Closing Steel session...")
    try:
        client.sessions.release(session_id)
    except Exception as e:
        logger.error(f"Error releasing Steel session: {str(e)}")

def get_context(session_id):
    logger.info("Get Steel session context...")
    context = client.sessions.context(session_id)
    return context


class SteelBrowserService(BrowserService):
    steel_session: SessionResponse = None

    async def create_session(self, context, session_timeout):
        self.steel_session = create_steel_session(context, session_timeout)
        id = self.steel_session.id
        cdp_url = f"wss://connect.steel.dev?apiKey={os.environ["STEEL_API_KEY"]}&sessionId={id}"
        debug_url = self.steel_session.session_viewer_url
                
        return {
            "id": id,
            "cdp_url": cdp_url,
            "debug_url": debug_url,
        }

    async def close_session(self):
        if self.steel_session:
            release_steel_session(self.steel_session.id)