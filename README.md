# Webagent

🚀 Call web agent through APIs!

A very simple web agent server using excellent [Browser-use tool](https://github.com/browser-use/browser-use).
- 🌐 Multiple LLM compatibility
- 🔒 Hosted on your infrastructure

## Installation

### Option 1: Local Installation

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

### Option 2: Docker Installation

#### Using Docker

1. Build the Docker image:

```bash
docker build -t webagent .
```

2. Run the container:

```bash
docker run -p 8080:8080 --env-file .env webagent
```

The Docker image includes all necessary dependencies, including Playwright for browser automation.

#### Using Docker Compose

1. Configure your environment variables in the `docker-compose.yml` file or in a `.env` file.

2. Start the service:

```bash
docker-compose up
```

## Starting the server

### Local Start

```bash
python server.py
```

### Docker Start

```bash
# Using Docker
docker run -p 8080:8080 --env-file .env webagent

# Using Docker Compose
docker-compose up
```

The server will start at http://localhost:8080

## API Documentation

Once the server is started, you can access the interactive API documentation at:

- http://localhost:8080/docs (Swagger UI)
- http://localhost:8080/redoc (ReDoc)

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
  'http://localhost:8080/run' \
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
base_url = "http://localhost:8080"

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
