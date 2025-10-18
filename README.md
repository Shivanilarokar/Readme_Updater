# 🤖 AutoDoc Agent

An AI-powered agent that automatically analyzes code changes in GitHub repositories and updates README.md files accordingly.

## 🚀 How It Works

1. **GitHub Push** → Webhook triggers the agent
2. **Change Detection** → Extracts commit details and changed files
3. **Diff Analysis** → Fetches detailed diffs using GitHub API
4. **AI Processing** → LLM analyzes changes and generates README updates
5. **Auto-Commit** → Updated README is committed back to GitHub

## 📋 Prerequisites

- Python 3.10+
- GitHub Personal Access Token
- OpenAI API Key

## 🛠️ Setup

1. **Install dependencies**
   ```bash
   pip install -r Requirements.txt
   ```

2. **Set environment variables**
   ```bash
   export TOKEN_GITHUB=your_github_token
   export OPENAI_API_KEY=your_openai_key
   ```

3. **Run the application**
   ```bash
   uvicorn Fastweb:app --host 0.0.0.0 --port 8000
   ```

4. **Configure GitHub Webhook**
   - URL: `https://your-app-url.com/webhook`
   - Content type: `application/json`
   - Events: "Just the push event"

## 📁 Core Files

- `Fastweb.py` - FastAPI webhook endpoint
- `Readme_Updater_agent.py` - AI agent logic
- `githubapitoolcall.py` - GitHub API integration
- `State.py` - State management
- `Requirements.txt` - Dependencies
- `Dockerfile` - Docker configuration

## 🚀 Deployment

### Docker
```bash
docker build -t autodoc-agent .
docker run -p 8000:8000 -e TOKEN_GITHUB=your_token -e OPENAI_API_KEY=your_key autodoc-agent
```

### Cloud Platforms
Deploy to Render, Heroku, or any cloud platform using the Dockerfile.

## 📝 API Endpoints

- `GET /` - Health check
- `POST /webhook` - GitHub webhook receiver
