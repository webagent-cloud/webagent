import os
from .browser_service import BrowserService
from .local_browser_service import LocalBrowserService
from .steel_browser_service import SteelBrowserService
from .browserbase_browser_service import BrowserbaseBrowserService

def get_browser_service() -> BrowserService:
    environment = os.getenv('BROWSER_PROVIDER', 'local')
    
    if environment == 'local':
        return LocalBrowserService()
    elif environment == 'steel':
        return SteelBrowserService()
    elif environment == 'browserbase':
        return BrowserbaseBrowserService()