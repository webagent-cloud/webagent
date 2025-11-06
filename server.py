import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["DISABLE_TELEMETRY"] = "true"
os.environ["BROWSER_USE_CLOUD_SYNC"] = "false"
os.environ["ANONYMIZED_TELEMETRY"] = "false"
if os.getenv("ENVIRONMENT") == "dev":
    DEV_ENVIRONMENT = True
else:
    DEV_ENVIRONMENT = False

if __name__ == "__main__":
    uvicorn.run(
        "webagent.api:app",
        host="0.0.0.0",
        port=8080,
        reload=DEV_ENVIRONMENT,
        loop="asyncio"  # Use standard asyncio instead of uvloop for compatibility with nest_asyncio
    )
