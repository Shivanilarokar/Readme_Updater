# readme_updateragent.py

import os
import json
import logging
import requests
import time
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from State import RepoState

# ---------------- Logging ----------------
logger = logging.getLogger("readme_updater_agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# ---------------- Enhanced Prompts ----------------
SYSTEM_PROMPT = """
You are an expert technical writer and README designer for GitHub repositories. 
Your task is to create beautiful, professional, and comprehensive README.md files.

GUIDELINES:
1. Create aesthetic, well-structured Markdown with proper formatting
2. Use emojis, badges, and visual elements to make it engaging
3. Include clear sections: Overview, Features, Installation, Usage, Examples
4. Add code examples with syntax highlighting
5. Include badges for build status, version, license, etc.
6. Make it professional yet approachable
7. Focus on what the code does and how to use it
8. Include proper headings, lists, and formatting

STYLE:
- Use clear, concise language
- Add relevant emojis for visual appeal
- Include code blocks with proper syntax highlighting
- Use tables for structured information
- Add badges and shields for professional look
- Include installation and usage instructions
"""

USER_PROMPT_TEMPLATE = """
# Repository Analysis Request

## Repository Information:
- **Repository**: {repo}
- **Owner**: {owner}
- **Branch**: {branch}
- **Pusher**: {pusher}
- **Repository URL**: {repository_url}
- **Compare URL**: {compare_url}

## Recent Changes:
**Commit Messages:**
{commit_messages}

**Files Changed:**
{changed_files}

**Detailed Diff Data:**
{diff_data}

## Task:
Create a comprehensive, beautiful, and professional README.md for this repository based on the actual code changes and file contents.

REQUIREMENTS:
1. **Aesthetic Design**: Use emojis, badges, proper formatting
2. **Comprehensive Content**: Include all necessary sections
3. **Code Examples**: Show actual code snippets from the files
4. **Professional Structure**: Clear headings, lists, tables
5. **Installation Guide**: How to set up and run the code
6. **Usage Examples**: Practical examples of how to use the code
7. **Features List**: What the repository offers
8. **Contributing Guidelines**: How others can contribute

Make it look like a professional open-source project README that developers would want to use and contribute to.
"""

# ---------------- Model ----------------
def get_llm():
    """Get LLM instance with proper error handling."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("⚠️ OPENAI_API_KEY not found - LLM will not work without it")
        return None
    
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=api_key,
        temperature=0.6,
    )

# ---------------- GitHub API Functions ----------------
def commit_readme_to_github(owner: str, repo: str, content: str, commit_message: str = "🤖 Auto-update README.md"):
    """
    Commit the updated README.md to GitHub repository.
    """
    try:
        token = os.getenv("TOKEN_GITHUB") or os.getenv("GITHUB_TOKEN")
        if not token:
            logger.error("❌ Missing GitHub token for committing changes")
            return {"error": "Missing GitHub token"}

        # Get current README content to get SHA
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/README.md"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {token}",
        }
        
        logger.info(f"🔍 GitHub API URL: {url}")
        logger.info(f"🔍 Owner: {owner}, Repo: {repo}")

        # Get current file info
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            logger.info("📝 README.md doesn't exist, will create new one")
            sha = None
        elif response.status_code == 200:
            file_data = response.json()
            sha = file_data["sha"]
            logger.info("📝 Found existing README.md, will update it")
        else:
            logger.error(f"❌ Error fetching README: {response.status_code}")
            return {"error": f"Failed to fetch README: {response.status_code}"}

        # Prepare commit data
        import base64
        content_bytes = content.encode('utf-8')
        content_b64 = base64.b64encode(content_bytes).decode('utf-8')

        commit_data = {
            "message": commit_message,
            "content": content_b64,
            "branch": "master"  # Use master branch
        }

        if sha:
            commit_data["sha"] = sha

        # Commit the file
        logger.info(f"🔍 Making GitHub API request to: {url}")
        logger.info(f"🔍 Commit data: {commit_data}")
        response = requests.put(url, headers=headers, json=commit_data)
        
        logger.info(f"🔍 GitHub API response: {response.status_code}")
        logger.info(f"🔍 Response text: {response.text[:500]}")
        
        if response.status_code in [200, 201]:
            commit_data = response.json()
            commit_sha = commit_data.get("commit", {}).get("sha")
            commit_url = commit_data.get("html_url", "")
            
            logger.info("✅ Successfully committed README.md to GitHub")
            logger.info(f"🔗 Commit URL: {commit_url}")
            logger.info(f"📝 Commit SHA: {commit_sha}")
            
            return {"success": True, "commit_sha": commit_sha, "commit_url": commit_url}
        else:
            logger.error(f"❌ Error committing README: {response.status_code} - {response.text}")
            logger.info("🔄 Attempting to create a Pull Request instead...")
            
            # Try to create a PR as fallback
            pr_result = create_pull_request(owner, repo, readme_text, commit_message)
            if "error" not in pr_result:
                return {"success": True, "pr_url": pr_result.get("html_url"), "pr_number": pr_result.get("number")}
            else:
                return {"error": f"Failed to commit: {response.status_code} - {response.text}"}

    except Exception as e:
        logger.exception(f"❌ Exception committing README: {e}")
        return {"error": str(e)}

def create_branch_with_readme(owner: str, repo: str, branch_name: str, readme_content: str, commit_message: str):
    """
    Create a new branch and commit README to it.
    """
    try:
        token = os.getenv("TOKEN_GITHUB") or os.getenv("GITHUB_TOKEN")
        if not token:
            return {"error": "Missing GitHub token"}

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {token}",
        }

        # Step 1: Get the latest commit SHA from master branch
        ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/master"
        response = requests.get(ref_url, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"❌ Failed to get master branch: {response.status_code}")
            return {"error": f"Failed to get master branch: {response.status_code}"}
        
        master_sha = response.json()["object"]["sha"]
        logger.info(f"🔍 Master branch SHA: {master_sha}")

        # Step 2: Create new branch from master
        branch_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
        branch_data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": master_sha
        }
        
        logger.info(f"🔍 Creating branch: {branch_name}")
        response = requests.post(branch_url, headers=headers, json=branch_data)
        
        if response.status_code not in [200, 201]:
            logger.error(f"❌ Failed to create branch: {response.status_code} - {response.text}")
            return {"error": f"Failed to create branch: {response.status_code}"}
        
        logger.info(f"✅ Successfully created branch: {branch_name}")

        # Step 3: Commit README to the new branch
        import base64
        content_bytes = readme_content.encode('utf-8')
        content_b64 = base64.b64encode(content_bytes).decode('utf-8')

        commit_data = {
            "message": commit_message,
            "content": content_b64,
            "branch": branch_name
        }

        readme_url = f"https://api.github.com/repos/{owner}/{repo}/contents/README.md"
        logger.info(f"🔍 Committing README to branch: {branch_name}")
        response = requests.put(readme_url, headers=headers, json=commit_data)
        
        if response.status_code in [200, 201]:
            logger.info("✅ Successfully committed README to branch")
            return {"success": True, "branch_name": branch_name}
        else:
            logger.error(f"❌ Failed to commit README: {response.status_code} - {response.text}")
            return {"error": f"Failed to commit README: {response.status_code}"}
            
    except Exception as e:
        logger.exception(f"❌ Exception creating branch: {e}")
        return {"error": str(e)}

def create_pull_request(owner: str, repo: str, branch_name: str, commit_message: str):
    """
    Create a Pull Request from the branch.
    """
    try:
        token = os.getenv("TOKEN_GITHUB") or os.getenv("GITHUB_TOKEN")
        if not token:
            return {"error": "Missing GitHub token"}

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {token}",
        }
        
        # Create the PR
        pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        pr_data = {
            "title": commit_message,
            "head": branch_name,
            "base": "master",
            "body": f"""🤖 Auto-generated README update

## Summary
This PR contains an automatically generated README update based on recent code changes.

## Changes Made
- Updated README.md with comprehensive documentation
- Added proper formatting and structure
- Included code examples and usage instructions
- Enhanced with badges and visual elements

## Generated by AutoDoc Agent
This README was automatically generated by the AutoDoc Agent based on the recent code changes in your repository.

Please review the changes and merge if they look good! 🚀"""
        }
        
        logger.info(f"🔍 Creating PR: {pr_data['title']}")
        response = requests.post(pr_url, headers=headers, json=pr_data)
        
        if response.status_code in [200, 201]:
            pr_data = response.json()
            logger.info("✅ Successfully created Pull Request")
            logger.info(f"🔗 PR URL: {pr_data.get('html_url')}")
            return {"success": True, "html_url": pr_data.get("html_url"), "number": pr_data.get("number")}
        else:
            logger.error(f"❌ Failed to create PR: {response.status_code} - {response.text}")
            return {"error": f"Failed to create PR: {response.status_code}"}
            
    except Exception as e:
        logger.exception(f"❌ Exception creating PR: {e}")
        return {"error": str(e)}

# ---------------- Node Logic ----------------
def generate_updated_readme(state: RepoState):
    """
    🚀 Enhanced README generator with branch creation and PR workflow.
    Uses actual diff data and creates professional READMEs.
    """
    try:
        logger.info("🚀 Starting enhanced README update agent...")
        logger.info(f"🔍 Repository: {state.get('owner')}/{state.get('repo')}")
        logger.info(f"🔍 Branch: {state.get('branch')}")
        logger.info(f"🔍 Files changed: {state.get('total_files_changed', 0)}")

        # Validate required state data
        if not state.get("files") or len(state.get("files", [])) == 0:
            logger.warning("⚠️ No diff data found in state")
            return {"messages": [{"role": "assistant", "content": "No changes detected to generate README"}]}
        
        # Prepare comprehensive data for LLM
        commit_messages = "\n".join([f"- {msg}" for msg in state.get("messages", [])])
        changed_files = "\n".join([f"- {file.get('filename', file)}" for file in state.get("files", [])])
        diff_content = json.dumps(state.get("files", []), indent=2)
        
        logger.info(f"🔍 Processing {len(state.get('files', []))} files with actual diff data")
        logger.info(f"🔍 Commit messages: {commit_messages[:100]}...")
        
        # Create enhanced prompt with all context
        prompt = USER_PROMPT_TEMPLATE.format(
            repo=state["repo"],
            owner=state.get("owner", "Shivanilarokar"),
            branch=state.get("branch", "master"),
            pusher=state.get("pusher", "unknown"),
            repository_url=state.get("repository_url", ""),
            compare_url=state.get("compare_url", ""),
            commit_messages=commit_messages,
            changed_files=changed_files,
            diff_data=diff_content
        )

        logger.info("🧠 Generating comprehensive README via LLM...")
        llm = get_llm()
        if not llm:
            logger.error("❌ Cannot generate README without OpenAI API key")
            return {"messages": [f"Error: OpenAI API key not found"]}
        
        response = llm.invoke(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
        )

        readme_text = response.content.strip()
        logger.info(f"✅ Generated README ({len(readme_text)} characters)")

        # Save locally for backup
        os.makedirs("data", exist_ok=True)
        output_path = os.path.join("data", "UPDATED_README.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(readme_text)
        logger.info(f"✅ README saved locally → {output_path}")

        # 🌿 Create branch and PR workflow
        logger.info("🌿 Creating branch and Pull Request workflow...")
        branch_name = f"autodoc-readme-update-{int(time.time())}"
        commit_message = f"🤖 Auto-update README.md based on changes in {state['base_sha'][:7] if state['base_sha'] else 'unknown'}...{state['head_sha'][:7] if state['head_sha'] else 'unknown'}"
        
        logger.info(f"🔍 Creating branch: {branch_name}")
        logger.info(f"🔍 Commit message: {commit_message}")
        
        # Step 1: Create branch with README
        logger.info("📝 Step 1: Creating branch and committing README...")
        branch_result = create_branch_with_readme(
            owner=state.get("owner", "Shivanilarokar"),
            repo=state["repo"],
            branch_name=branch_name,
            readme_content=readme_text,
            commit_message=commit_message
        )
        
        if "error" in branch_result:
            logger.error(f"❌ Failed to create branch: {branch_result['error']}")
            return {
                "repo": state["repo"],
                "owner": state.get("owner"),
                "base_sha": state["base_sha"],
                "head_sha": state["head_sha"],
                "total_files_changed": state["total_files_changed"],
                "files": state["files"],
                "messages": [{"role": "assistant", "content": readme_text}],
                "branch_success": False,
                "branch_error": branch_result["error"],
                "pr_success": False
            }
        
        logger.info(f"✅ Successfully created branch: {branch_name}")
        
        # Step 2: Create Pull Request
        logger.info("📝 Step 2: Creating Pull Request...")
        pr_result = create_pull_request(
            owner=state.get("owner", "Shivanilarokar"),
            repo=state["repo"],
            branch_name=branch_name,
            commit_message=commit_message
        )
        
        if "error" in pr_result:
            logger.error(f"❌ Failed to create PR: {pr_result['error']}")
            return {
                "repo": state["repo"],
                "owner": state.get("owner"),
                "base_sha": state["base_sha"],
                "head_sha": state["head_sha"],
                "total_files_changed": state["total_files_changed"],
                "files": state["files"],
                "messages": [{"role": "assistant", "content": readme_text}],
                "branch_success": True,
                "branch_name": branch_name,
                "pr_success": False,
                "pr_error": pr_result["error"]
            }
        
        pr_url = pr_result.get("html_url")
        pr_number = pr_result.get("number")
        
        logger.info(f"✅ Successfully created Pull Request!")
        logger.info(f"🔗 PR URL: {pr_url}")
        logger.info(f"📝 PR Number: {pr_number}")
        logger.info(f"🌿 Branch: {branch_name}")
        
        return {
            "repo": state["repo"],
            "owner": state.get("owner"),
            "base_sha": state["base_sha"],
            "head_sha": state["head_sha"],
            "total_files_changed": state["total_files_changed"],
            "files": state["files"],
            "messages": [{"role": "assistant", "content": readme_text}],
            "branch_success": True,
            "branch_name": branch_name,
            "pr_success": True,
            "pr_url": pr_url,
            "pr_number": pr_number
        }

    except Exception as e:
        logger.exception("❌ Error generating README")
        return {"messages": [f"Error: {e}"]}

# ---------------- Build LangGraph ----------------
graph = StateGraph(RepoState)
graph.add_node("update_readme", generate_updated_readme)
graph.add_edge(START, "update_readme")
graph.add_edge("update_readme", END)

readme_updater = graph.compile()
