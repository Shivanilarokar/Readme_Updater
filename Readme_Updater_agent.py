# readme_updateragent.py

import os
import json
import logging
import requests
import time
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from githubapitoolcall import fetch_commit_diffs
from State import RepoState

# ---------------- Logging ----------------
logger = logging.getLogger("readme_updater_agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# ---------------- Prompts ----------------
SYSTEM_PROMPT = (
    "You are a professional developer-focused technical writer and README designer. "
    "Produce clear, concise, and aesthetic README content suitable for an open-source GitHub repo. "
    "Focus on: summary, highlights, small before/after examples, breaking changes, and test steps. "
    "Write beautiful Markdown."
)

USER_PROMPT_TEMPLATE = """
Repository: {repo}
Base commit: {base}
Head commit: {head}

Here are the diffs (unified patch format):
{diffs}

Write a README.md update that:
- Summarizes the change clearly (2–4 paragraphs)
- Lists what changed and why
- Shows small code examples if relevant
- Ends with a 'How to test' section
- Add JSON metadata in a fenced block:
  summary_lines, important_files, version_note
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

def create_pull_request(owner: str, repo: str, content: str, commit_message: str):
    """
    Create a Pull Request with the updated README as fallback.
    """
    try:
        token = os.getenv("TOKEN_GITHUB") or os.getenv("GITHUB_TOKEN")
        if not token:
            return {"error": "Missing GitHub token"}

        # Create a new branch
        branch_name = f"autodoc-readme-update-{int(time.time())}"
        
        # First, create the branch
        branch_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
        branch_data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": "master"  # or get from API
        }
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {token}",
        }
        
        logger.info(f"🔍 Creating branch: {branch_name}")
        response = requests.post(branch_url, headers=headers, json=branch_data)
        
        if response.status_code not in [200, 201]:
            logger.error(f"❌ Failed to create branch: {response.status_code}")
            return {"error": f"Failed to create branch: {response.status_code}"}
        
        # Now create the PR
        pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        pr_data = {
            "title": commit_message,
            "head": branch_name,
            "base": "master",
            "body": f"🤖 Auto-generated README update\n\nThis PR contains an automatically generated README update based on recent code changes."
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
    Node that fetches diffs (if needed) and generates README using LLM.
    """
    try:
        logger.info("🚀 Starting README update agent...")

        # If no diff data is provided in state, fetch it
        if not state.get("files") or len(state.get("files", [])) == 0:
            logger.info("🔍 No diff data found in state — calling fetch_commit_diffs...")
            diff_data = fetch_commit_diffs(
                owner=state.get("owner", "shivanilarokar"),
                repo=state["repo"],
                base_sha=state["base_sha"],
                head_sha=state["head_sha"],
            )

            if "error" in diff_data:
                logger.error(f"❌ Error fetching diffs: {diff_data['error']}")
                return {"messages": [f"❌ Error fetching diffs: {diff_data['error']}"]}

            state["files"] = diff_data.get("files", [])
            state["total_files_changed"] = diff_data.get("total_files_changed", 0)

        # Convert diffs to string for LLM
        diffs = json.dumps(state["files"], indent=2)
        prompt = USER_PROMPT_TEMPLATE.format(
            repo=state["repo"],
            base=state["base_sha"],
            head=state["head_sha"],
            diffs=diffs,
        )

        logger.info("🧠 Generating updated README via LLM...")
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

        # Save locally for backup
        os.makedirs("data", exist_ok=True)
        output_path = os.path.join("data", "UPDATED_README.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(readme_text)

        logger.info(f"✅ README saved locally → {output_path}")

        # Commit to GitHub
        logger.info("📤 Committing updated README to GitHub...")
        logger.info(f"🔍 Committing to: {state.get('owner', 'Shivanilarokar')}/{state['repo']}")
        logger.info(f"🔍 README content length: {len(readme_text)} characters")
        
        try:
            commit_result = commit_readme_to_github(
                owner=state.get("owner", "Shivanilarokar"),
                repo=state["repo"],
                content=readme_text,
                commit_message=f"🤖 Auto-update README.md based on changes in {state['base_sha'][:7] if state['base_sha'] else 'unknown'}...{state['head_sha'][:7] if state['head_sha'] else 'unknown'}"
            )
            logger.info(f"🔍 Commit result: {commit_result}")
        except Exception as commit_error:
            logger.error(f"❌ Exception during GitHub commit: {commit_error}")
            commit_result = {"error": str(commit_error)}

        if "error" in commit_result:
            logger.error(f"❌ Failed to commit to GitHub: {commit_result['error']}")
            return {
                "repo": state["repo"],
                "owner": state.get("owner"),
                "base_sha": state["base_sha"],
                "head_sha": state["head_sha"],
                "total_files_changed": state["total_files_changed"],
                "files": state["files"],
                "messages": [{"role": "assistant", "content": readme_text}],
                "commit_error": commit_result["error"]
            }
        else:
            if "pr_url" in commit_result:
                logger.info("✅ Successfully created Pull Request")
                logger.info(f"🔗 View your PR at: {commit_result.get('pr_url', 'N/A')}")
                return {
                    "repo": state["repo"],
                    "owner": state.get("owner"),
                    "base_sha": state["base_sha"],
                    "head_sha": state["head_sha"],
                    "total_files_changed": state["total_files_changed"],
                    "files": state["files"],
                    "messages": [{"role": "assistant", "content": readme_text}],
                    "pr_success": True,
                    "pr_url": commit_result.get("pr_url"),
                    "pr_number": commit_result.get("pr_number")
                }
            else:
                logger.info("✅ Successfully committed README to GitHub")
                logger.info(f"🔗 View your updated README at: {commit_result.get('commit_url', 'N/A')}")
                return {
                    "repo": state["repo"],
                    "owner": state.get("owner"),
                    "base_sha": state["base_sha"],
                    "head_sha": state["head_sha"],
                    "total_files_changed": state["total_files_changed"],
                    "files": state["files"],
                    "messages": [{"role": "assistant", "content": readme_text}],
                    "commit_success": True,
                    "commit_sha": commit_result.get("commit_sha"),
                    "commit_url": commit_result.get("commit_url")
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
