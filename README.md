<div align="center">
  <img src="frontend/src/assets/logo.png" alt="WebAgent Logo" width="200"/>
</div>

🚀 Build fast and reliable AI browser agents !

Webagent uses AI to build complex browser workflows from simple prompts.

```
curl -X POST http://localhost:3000/runs \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Go to https://webagent.cloud and explain what the platform does."
  }'
```

### Fast and reliable.

🚀 Webagent can record and cache browser actions to build parameterized workflows, then replay repetitive tasks without using AI — fast and cost-effective.
💊 Workflows are self-healing: if a website changes, the workflow falls back to AI.

### Adaptable.

- 🔒 Self-Host on your infrastructure
- 🔗 Integrate into any app with the API, or n8n, Zapier, Make integrations.
- 🌐 Multiple LLM compatibility
- 🔎 Supports multiple Browsers sources: Local, Steel, Browserbase
- 🔌 Compatible with multiple AI agent engine : Browser-use, Notte, Stagehand (soon)


### And many more !
- 💽 Store and retrieve results in database
- 🪝 Get notified of results with webhooks
- 🗄️ Structure results with JSON Schema
- 🍪 Reuse sessions and cookies with authentication contexts (soon)

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
GEMINI_API_KEY=

BROWSER_PROVIDER=local # local | browserbase | steel
# Provide browser provider API keys if needed
STEEL_API_KEY=****
BROWSERBASE_PROJECT_ID=******
BROWSERBASE_API_KEY=******
```

4. Run the server

```bash
python server.py
```

Go on http://localhost:8080 and start automating !

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

Go on http://localhost:8080 and start automating !

## API Documentation

The documentation is available at https://docs.webagent.cloud/self-hosted-api-reference/introduction