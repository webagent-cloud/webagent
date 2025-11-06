import logging
from .browser_service import BrowserService

from dotenv import load_dotenv
import os
from browserbase import Browserbase


logger = logging.getLogger(__name__)

async def create_browserbase_session(session_timeout):
    load_dotenv()

    bb = Browserbase(api_key=os.environ["BROWSERBASE_API_KEY"])
    session = bb.sessions.create(
        project_id=os.environ["BROWSERBASE_PROJECT_ID"],
        api_timeout=session_timeout,
    )

    return session


class BrowserbaseBrowserService(BrowserService):
    browserbase_session = None

    async def create_session(self, session_timeout):
        self.browserbase_session = await create_browserbase_session(session_timeout)
        cdp_url = self.browserbase_session.connect_url
        id = self.browserbase_session.connect_url
        debug_url = f"https://www.browserbase.com/sessions/{self.browserbase_session.id}"

        return {
            "id": id,
            "cdp_url": cdp_url,
            "debug_url": debug_url
        }

    async def close_session(self):
        # browserbase does not have an API to close/release a session
        if self.browserbase_session:
            self.browserbase_session = None