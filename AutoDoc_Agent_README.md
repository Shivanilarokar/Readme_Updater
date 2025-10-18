
# 🤖 AutoDoc Agent
### “Let your AI handle the docs while you code.”

![AutoDoc Agent Banner](https://img.shields.io/badge/AI%20Doc%20Automation-AutoDoc%20Agent-blueviolet?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/framework-FastAPI-teal?style=for-the-badge)
![LangChain](https://img.shields.io/badge/AI%20Powered-LangChain-orange?style=for-the-badge)

---

## 🧠 Overview
**AutoDoc Agent** is an AI-powered documentation assistant that automatically analyzes your GitHub code changes and updates your repository’s `README.md` intelligently — saving you time and keeping your project docs always up to date. 


  ✅ **Detects accurate changes** from push events
  ✅ **Generates context aware READMEs** based on actual code analysis
  ✅ **Creates branches and PRs** for safe updates
  ✅ **Provides comprehensive logging** for monitoring

---

## ⚙️ Architecture Flow

![Architecture](https://mermaid.ink/img/pako:eNqFUl1v2zAM_Sv0FyQCAhU8q0E2uZYmKnWvHzWEo4UpuIm4YxVw2fz3xqEkKiZbQK7_g6PbM9c_J4vN0YF8ePyzfRAsS8oSHvAPnJssMEFxMaW7RMTXmh9DA6CScyJcV6VKO_pYTi_pU8K8zstHZ9YBKPfuI8V2x6clJ0LJHecOADG6tE7j3I-MYut2G5IdaeD7eBgaU5Sr8tk7P0KZrJ7VQ6hrhhrc3TyyJPGOsR2cJ-3QObKqlAjLwbG3iPkf5QpAdQ14nl3H3I8eC7PG6b5OfCN4xGXLvMeMZxA4B8e0Wn5S_RyY4nXn0eMW6Kco9R-ZJxYx4p4Q9wX5qfZaYfWxZMYq6S8Yj5izQv53Y85I2SK4tr7j0Ck10azrT2_wRUIwK)

---

## 🚀 How It Works
1. **GitHub Push** → A new push triggers your FastAPI webhook  
2. **Change Detection** → Extracts commit SHAs and changed files  
3. **Diff Analysis** → Uses the GitHub API tool to fetch detailed diffs  
4. **AI Processing** → The LLM (OpenAI) analyzes changes and generates README updates  
5. **Auto Commit** → The updated README is committed or PR’ed back to the repo   



🎯 **Benefits:**

1. **Accurate Analysis**: Uses real diff data instead of just file names
2. **Professional READMEs**: Beautiful, comprehensive documentation
3. **Safe Workflow**: Creates PRs instead of direct commits
4. **Review Process**: You can review and approve changes
5. **Better Logging**: Detailed logs for debugging
6. **Context-Aware**: Understands what actually changed in your code


---

## 📋 Prerequisites
- 🐍 Python 3.10+
- 🔑 GitHub Personal Access Token
- 🧠 OpenAI API Key
- ☁️ (Optional) Azure / Render / Any Cloud for hosting

---

## 🛠️ Setup
1️⃣ Clone the repository  
```bash
git clone https://github.com/Shivanilarokar/Readme_Updater
cd AutoDocAgent
```

2️⃣ Install dependencies  
```bash
pip install -r Requirements.txt
```

3️⃣ Configure environment variables  
```bash
export TOKEN_GITHUB=your_github_token
export OPENAI_API_KEY=your_openai_key
```

4️⃣ Run the FastAPI app  
```bash
uvicorn Fastweb:app --host 0.0.0.0 --port 8000
```

5️⃣ Configure GitHub Webhook  
Payload URL → `https://autodocagent-fwfhc7bvgmccahdy.centralindia-01.azurewebsites.net/webhook`  
Event → `push`

---

## 🧩 Core Components
| File | Description |
|------|--------------|
| Fastweb.py | FastAPI webhook endpoint |
| Readme_Updater_agent.py | LLM-based README generator |
| githubapitoolcall.py | LangChain tool for GitHub diff fetching |
| State.py | Repo state manager for LangGraph |
| Requirements.txt | Dependencies |
| Dockerfile | Docker container setup For Azure Deployment |

---

## 🚀 Deployment

### Docker
```bash
docker build -t fastapi-webhook .
docker tag fastapi-webhook shivanilarokar/fastapi-webhook:latest
docker push shivanilarokar/fastapi-webhook:latest   

```

### Cloud
Deployed  on Azure Web App using Docker container.

---

## 🧪 API Endpoints
| Method | Endpoint | Description |
|--------|-----------|-------------|
| GET | / | Health check |
| POST | /webhook | GitHub webhook receiver |

---

## 👨‍💻 Author
**Shivani Larokar**  
[GitHub Profile](https://github.com/Shivanilarokar)  

Built with ❤️ using FastAPI, LangGraph, and OpenAI APIs.

---

## 📜 License
MIT License — Free for personal and commercial use.
