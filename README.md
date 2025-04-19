# Webagent

🚀 Call web agent through APIs!

A very simple web agent server using excellent [Browser-use tool](https://github.com/browser-use/browser-use).
- 🌐 Multiple LLM compatibility
- 🔒 Hosted on your infrastructure

## Installation

1. Make sure you have Python 3.12+ installed.
2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Configure your `.env` file with the necessary environment variables (API keys, etc.)
Add your API keys for the provider you want to use to your .env file.

```
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
AZURE_ENDPOINT=
AZURE_OPENAI_API_KEY=
GEMINI_API_KEY=
DEEPSEEK_API_KEY=
GROK_API_KEY=
NOVITA_API_KEY=
```

## Starting the server

```bash
python server.py
```

The server will start at http://localhost:8000

## API Documentation

Once the server is started, you can access the interactive API documentation at:

- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## Using the API

### Execute a task with the agent

**Endpoint**: `POST /run`

**Request body**:
```json
{
  "task": "go to this site https://example.com and retrieve the page title",
  "provider": "openai",
  "model": "gpt-4o"
}
```

**Response**:
```json
{
  "history": [
    {
      "is_done": true,
      "success": true,
      "extracted_content": "Example Domain",
      "error": null,
      "include_in_memory": false
    }
  ],
  "result": "Example Domain",
  "is_done": true,
  "is_successful": true,
  "status": "success",
  "screenshots": [
    "data:image/png;base64,..."
  ]
}
```

## Example usage with curl

```bash
# Execute a task
curl -X 'POST' \
  'http://localhost:8000/run' \
  -H 'Content-Type: application/json' \
  -d '{
  "task": "go to this site https://example.com and retrieve the page title",
  "model": "gpt-4o",
  "provider": "openai"
}'
```

## Example usage with Python

```python
import requests

# Base URL of the API
base_url = "http://localhost:8000"

# Execute a task
response = requests.post(
    f"{base_url}/run",
    json={
        "task": "go to this site https://example.com and retrieve the page title",
        "model": "gpt-4o",
        "provider": "openai"
    }
)

# Print the response
print(f"Response: {response.json()}")
```
