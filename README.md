# OpenGuy

<div align="center">
  <img src="./logo.png" alt="OpenGuy Logo" width="300" style="border-radius: 10px;"/>
</div>

OpenGuy is an AI-powered robotics interface that uses Natural Language to deterministically control hardware via Python.

## Architecture

We have massively simplified and optimized the architecture to be incredibly robust while having zero build steps:

- **Backend:** FastAPI, providing async route handlers, WebSocket connectivity, and local SQLite persistence for command history. It runs directly on your robot or local computer.
- **Frontend:** A single, premium `index.html` file using Tailwind CSS and Vue.js via CDN. This allows it to be hosted *anywhere* (including Vercel natively) without any Node.js `npm build` steps, while retaining real-time communication via WebSockets.

## Running Locally

The smart installer handles everything — it checks for Python 3.12 and Git, installs them if missing, clones the repo, installs dependencies, and starts the server.

**Windows** (paste into PowerShell or CMD):
```
curl -o install.bat https://raw.githubusercontent.com/OPENEHIRA/OpenGuy/main/install.bat && install.bat
```

**Mac / Linux** (paste into Terminal):
```bash
curl -sL https://raw.githubusercontent.com/OPENEHIRA/OpenGuy/main/install.sh | bash
```

The server will start automatically at `http://localhost:5000`.

## Hosting on Vercel
Because the frontend is a single `index.html` file at the root of the repository, Vercel will deploy it automatically!

Once your Vercel URL is live, open it in your browser and use the **Backend URL** input at the top to point the UI to your local robot's IP or ngrok tunnel (e.g. `http://192.168.1.10:5000`).

## Universal AI Provider Support
OpenGuy uses `litellm`, meaning you can use **any API key on earth** (Groq, OpenAI, Anthropic, Gemini, etc.).

By default, it will attempt to use a fast, free open-source model (`groq/llama3-8b-8192`) if you provide a Groq key. You can override this by setting the `LLM_MODEL` environment variable.

**Examples (Windows):**
```powershell
# Using Groq (Default: llama3-8b-8192)
set GROQ_API_KEY="your-groq-key"

# Using OpenAI (GPT-4o)
set OPENAI_API_KEY="your-openai-key"
set LLM_MODEL="gpt-4o"

# Using Anthropic (Claude 3 Haiku)
set ANTHROPIC_API_KEY="your-anthropic-key"
set LLM_MODEL="claude-3-haiku-20240307"
```

**Examples (Mac/Linux):**
```bash
export GROQ_API_KEY="your-groq-key"
export LLM_MODEL="groq/llama3-8b-8192"
```
