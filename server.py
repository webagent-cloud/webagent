import uvicorn
from webagent.api import app

import os
os.environ["DISABLE_TELEMETRY"] = "true"
os.environ["BROWSER_USE_CLOUD_SYNC"] = "false"
os.environ["ANONYMIZED_TELEMETRY"] = "false"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
