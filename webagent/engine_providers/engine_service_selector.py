import os
from .engine_service import EngineService
from .notte_service import NotteService
from .browseruse_service import BrowseruseService

def get_engine_service() -> EngineService:
    environment = os.getenv('ENGINE_PROVIDER', 'browser-use')
    
    if environment == 'browser-use':
        return BrowseruseService()
    elif environment == 'notte':
        return NotteService()
    else:
        # Default to browser-use if unknown provider
        return BrowseruseService()
