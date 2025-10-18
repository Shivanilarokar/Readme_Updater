# 📁 AutoDoc Agent - Code Overview

## 🎯 What Each File Does:

### 1️⃣ **`Fastweb.py`** - Webhook Receiver & Entry Point
**Purpose**: Detects GitHub push events and triggers the agent
**What it does**:
- Receives webhooks from GitHub when you push code
- Extracts commit details (SHAs, changed files, author)
- Parses repository name and owner
- Triggers the README updater agent
- Logs all webhook activity

**Key Function**: `@app.post("/webhook")` - Main entry point

---

### 2️⃣ **`Readme_Updater_agent.py`** - Main AI Agent
**Purpose**: The brain of the system - analyzes changes and generates README updates
**What it does**:
- Fetches detailed diffs from GitHub API (if needed)
- Uses OpenAI to analyze code changes
- Generates intelligent README updates
- Commits updated README back to GitHub
- **NEW**: Logs the commit URL so you can see the result

**Key Functions**:
- `generate_updated_readme()` - Main workflow
- `commit_readme_to_github()` - Commits changes back

---

### 3️⃣ **`githubapitoolcall.py`** - GitHub API Integration
**Purpose**: Fetches detailed diffs between commits
**What it does**:
- Calls GitHub API to get file-by-file differences
- Extracts what changed, additions, deletions
- Saves diff data for the AI agent to analyze
- Handles GitHub API authentication

**Key Function**: `fetch_commit_diffs()` - Gets detailed change information

---

### 4️⃣ **`State.py`** - Data Structure
**Purpose**: Defines the data structure shared between components
**What it does**:
- Defines `RepoState` class with all necessary fields
- Ensures consistent data flow between webhook → agent → GitHub API
- Contains: repo, owner, branch, SHAs, files, messages

---

### 5️⃣ **`Requirements.txt`** - Dependencies
**Purpose**: Lists all Python packages needed
**What it does**:
- FastAPI for web server
- OpenAI for AI processing
- LangChain for agent framework
- Requests for GitHub API calls
- All with specific versions for stability

---

### 6️⃣ **`Dockerfile`** - Container Configuration
**Purpose**: Packages your app for deployment
**What it does**:
- Uses Python 3.10 base image
- Installs dependencies
- Exposes port 8000
- Runs your FastAPI app

---

### 7️⃣ **`.github/workflows/readme-update.yml`** - GitHub Actions Alternative
**Purpose**: Alternative way to run the agent (instead of webhooks)
**What it does**:
- Runs automatically when you push code
- Installs dependencies
- Runs the same agent logic
- Commits changes back to GitHub
- **Note**: This is an alternative to the webhook approach

---

## 🔄 Complete Workflow:

```
1. You push code to GitHub
   ↓
2. Fastweb.py receives webhook
   ↓
3. githubapitoolcall.py fetches diffs
   ↓
4. Readme_Updater_agent.py generates README
   ↓
5. Commits back to GitHub with URL logged
   ↓
6. You see updated README in your repo!
```

## 🚀 Two Ways to Run:

### Option A: Webhook (Recommended)
- Deploy Fastweb.py to cloud
- Configure GitHub webhook
- Automatic on every push

### Option B: GitHub Actions
- Uses the .yml file
- Runs in GitHub's servers
- No external deployment needed

## 📝 New URL Logging:
After README generation and commit, you'll see:
```
✅ Successfully committed README to GitHub
🔗 Commit URL: https://github.com/Shivanilarokar/DSA-Questions-/commit/abc123
📝 Commit SHA: abc123def456
🔗 View your updated README at: https://github.com/Shivanilarokar/DSA-Questions-/commit/abc123
```

**Your AutoDoc Agent is now complete with URL logging!** 🎉
