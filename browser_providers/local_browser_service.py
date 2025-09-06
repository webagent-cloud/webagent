import httpx
from playwright.async_api import async_playwright
from .browser_service import BrowserService

class LocalBrowserService(BrowserService):
    session = None
    async def create_session(self, session_timeout):
        p = await async_playwright().start()
        self.session = await p.chromium.launch(
            headless=False,
            args=["--remote-debugging-port=9222"]
        )
        client = httpx.AsyncClient()
        resp = await client.get("http://localhost:9222/json/version")
        data = resp.json()
        cdp_url = data["webSocketDebuggerUrl"]

        return {
            "id": "local",
            "cdp_url": cdp_url,
            "debug_url": None,
        }

    async def close_session(self):
        await self.session.close()
