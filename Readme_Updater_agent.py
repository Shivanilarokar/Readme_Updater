import os
import json
import base64
import logging
import requests
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from githubapitoolcall import fetch_commit_diffs
from State import RepoState  

# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("readme_updater_agent")

# ---------------- Prompts ----------------
SYSTEM_PROMPT = """
You are an expert technical documentation writer, context aware code detector between two commits and README designer for GitHub repositories.
Your task is to create professional, comprehensive, and visually appealing , ashthetic README.md files 
based on the repository’s latest code changes only .

Guidelines: 
- Identify the changes made in the code and generate a summery of the changes made in the code.
- Use clear Markdown structure: Overview, Features, Summery of the changes, Installation, Usage, and Example sections , some snippets of the code that are changed.
- Add emojis, badges, and formatted code examples.
- Keep it professional, concise, and readable.
- Make it look like a professional README.md file that developers would want to use and contribute to.
- No irrelevant information should be added to the README.md file.
"""

USER_PROMPT_TEMPLATE = """
# README Generation Request

## Repository Info
- Repository: {repo}
- Owner: {owner}
- Branch: {branch}
- Pusher: {pusher}
- Repository URL: {repository_url}
- Compare URL: {compare_url}

## Commit Messages
{commit_messages}

## Changed Files
{changed_files}

## Diff Data
{diff_data}

Please generate a complete and context aware README.md file that describes and summarizes the recent code changes in a professional manner.
"""

# ---------------- LLM Setup ----------------
def get_llm():
    """Get OpenAI LLM safely."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("❌ OPENAI_API_KEY not found.")
        return None

    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=api_key,
        temperature=0.6,
    )

# ---------------- GitHub API Function ----------------
def commit_readme_to_github(owner: str, repo: str, content: str, branch: str = "main") -> dict:
    """
    Create or update README.md in the main branch directly.
    """
    try:
        token = os.getenv("TOKEN_GITHUB") or os.getenv("GITHUB_TOKEN")
        if not token:
            logger.error("❌ Missing GitHub token.")
            return {"error": "Missing GitHub token"}

        url = f"https://api.github.com/repos/{owner}/{repo}/contents/README.md"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {token}",
        }

        # Get current README (if exists)
        response = requests.get(url, headers=headers)
        sha = response.json().get("sha") if response.status_code == 200 else None

        # Prepare commit data
        content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        commit_message = "🤖 Auto-update README.md with latest changes"
        commit_data = {"message": commit_message, "content": content_b64, "branch": branch}
        if sha:
            commit_data["sha"] = sha  # overwrite existing README.md

        response = requests.put(url, headers=headers, json=commit_data)
        if response.status_code in [200, 201]:
            data = response.json()
            html_url = data.get("content", {}).get("html_url", "")
            logger.info(f"✅ README successfully committed → {html_url}")
            return {"success": True, "readme_url": html_url}

        logger.error(f"❌ Failed to commit README: {response.status_code} - {response.text}")
        return {"error": response.text}

    except Exception as e:
        logger.exception(f"❌ Exception while committing README: {e}")
        return {"error": str(e)}

# ---------------- Core Agent Logic ----------------
def generate_updated_readme(state: RepoState):
    """
    Agent logic: fetch diffs → generate README → commit to main.
    """
    try:
        logger.info("🚀 Starting README update agent...")
        logger.info(f"🔍 Repo: {state['owner']}/{state['repo']} | Branch: {state['branch']}")

        # ✅ Fetch diffs using your tool (automatically)
        logger.info("🔧 Fetching commit diffs using GitHub tool...")
        diff_result = fetch_commit_diffs(
            owner=state["owner"],
            repo=state["repo"],
            base_sha=state["base_sha"],
            head_sha=state["head_sha"]
        )

        if "error" in diff_result:
            logger.error(f"❌ Diff fetch failed: {diff_result['error']}")
            return {"error": diff_result["error"]}

        state["files"] = diff_result.get("files", [])
        state["total_files_changed"] = diff_result.get("total_files_changed", len(state["files"]))

        if not state["files"]:
            logger.warning("⚠️ No file changes detected. Skipping README generation.")
            return {"messages": [{"role": "assistant", "content": "No changes detected."}]}

        # ✅ Prepare input for LLM
        commit_messages = "\n".join([f"- {msg}" for msg in state.get("commit_messages", [])])
        changed_files = "\n".join([f"- {f.get('filename')}" for f in state["files"]])
        diff_data = json.dumps(state["files"], indent=2)

        prompt = USER_PROMPT_TEMPLATE.format(
            repo=state["repo"],
            owner=state["owner"],
            branch=state["branch"],
            pusher=state.get("pusher", "unknown"),
            repository_url=state["repository_url"],
            compare_url=state["compare_url"],
            commit_messages=commit_messages,
            changed_files=changed_files,
            diff_data=diff_data
        )

        # ✅ Generate README content
        llm = get_llm()
        if not llm:
            return {"error": "Missing OpenAI API key"}

        logger.info("🧠 Generating README using LLM...")
        response = llm.invoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ])

        readme_text = response.content.strip()
        logger.info(f"✅ README generated ({len(readme_text)} chars)")

        # ✅ Commit README to GitHub (main branch)
        commit_result = commit_readme_to_github(state["owner"], state["repo"], readme_text, branch=state["branch"])
        if "error" in commit_result:
            return {"error": commit_result["error"]}

        # ✅ Save locally for backup
        os.makedirs("data", exist_ok=True)
        with open("data/UPDATED_README.md", "w", encoding="utf-8") as f:
            f.write(readme_text)

        state["readme_url"] = commit_result.get("readme_url")
        logger.info(f"🌐 Final README URL: {state['readme_url']}")
        return {"success": True, "readme_url": state["readme_url"]}

    except Exception as e:
        logger.exception("❌ Error generating README")
        return {"error": str(e)}

# ---------------- LangGraph ----------------
graph_builder = StateGraph(RepoState)
graph_builder.add_node("update_readme", generate_updated_readme)
graph_builder.add_edge(START, "update_readme")
graph_builder.add_edge("update_readme", END) 


readme_updater = graph_builder.compile()

# print graph builder 
readme_updater.get_graph().draw_mermaid_png(output_file_path="graph.png")