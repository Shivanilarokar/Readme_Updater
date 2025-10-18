from fastapi import FastAPI, Request 
import logging, sys, json, os
from Readme_Updater_agent import generate_updated_readme  # uses clean README generator agent
from githubapitoolcall import fetch_commit_diffs  # GitHub diff tool to fetch the diff between two commits

# ---------------- Logging setup (Azure-friendly) ----------------
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)
logger = logging.getLogger("main")

# ---------------- FastAPI App ----------------
app = FastAPI()

@app.get("/")
def home():
    """Basic health check endpoint."""
    logger.info("🚀 Health check passed")
    return {"message": "Hello from FastAPI Webhook!"}


# ---------------- GitHub Webhook Endpoint ----------------
@app.post("/webhook")
async def webhook(request: Request):
    """Receives push event payload from GitHub."""
    try:
        payload = await request.json()
        delivery_id = request.headers.get("X-GitHub-Delivery", "unknown")
        event_type = request.headers.get("X-GitHub-Event", "push")

        repo_full = payload["repository"]["full_name"]
        pusher = payload["pusher"]["name"]
        branch_ref = payload.get("ref", "")
        branch = branch_ref.split("/")[-1] if branch_ref else "unknown"

        logger.info(f"📦 New webhook delivery: {delivery_id}")
        logger.info(f"🔔 Event: {event_type}")
        logger.info(f"📁 Repo: {repo_full} | 👤 Pusher: {pusher} | 🌿 Branch: {branch}")

        commits = payload.get("commits", [])
        logger.info(f"🧩 Total commits: {len(commits)}")

        # Gather all changed files
        all_changed_files = []
        for commit in commits:
            added = commit.get("added", [])
            modified = commit.get("modified", [])
            removed = commit.get("removed", [])
            all_changed_files.extend(added + modified + removed)

        logger.info(f"🗂️ Changed files ({len(all_changed_files)}): {all_changed_files}")

        # Only trigger for relevant file types
        if not any(fname.endswith((".py", ".ipynb", "README.md")) for fname in all_changed_files):
            logger.info("ℹ️ No relevant files changed — skipping README generation.")
            return {"ok": True, "skipped": True}

        # Extract repo info
        owner, repo = repo_full.split("/")
        base_sha = payload.get("before", "")
        head_sha = payload.get("after", "")

        logger.info("🔧 Fetching commit diff data from GitHub API...")
        
        # StructuredTool → .invoke  tool call to fetch the diff between two commits
        diff_data = fetch_commit_diffs.invoke({
            "owner": owner,
            "repo": repo,
            "base_sha": base_sha,
            "head_sha": head_sha
        })

        if isinstance(diff_data, str):
            try:
                diff_data = json.loads(diff_data)
            except Exception:
                pass

        if not diff_data or "files" not in diff_data:
            logger.error(f"❌ Failed to fetch diff data: {diff_data}")
            return {"ok": False, "error": "No diff data returned"}

        logger.info(f"✅ Fetched diff for {diff_data.get('total_files_changed', 0)} files")

        # ✅ Build RepoState for the agent
        state = {
            "repo": repo,
            "owner": owner,
            "branch": branch,
            "base_sha": base_sha,
            "head_sha": head_sha,
            "total_files_changed": diff_data.get("total_files_changed", 0),
            "files": diff_data.get("files", []),
            "commit_messages": [c.get("message", "") for c in commits],
            "commit_details": commits,
            "pusher": pusher,
            "repository_url": payload["repository"]["html_url"],
            "compare_url": payload.get("compare", ""),
        }

        # ✅ Call README generation agent
        logger.info("🤖 Running README generator agent...")
        result = generate_updated_readme(state)

        if result.get("error"):
            logger.error(f"❌ README generation failed: {result['error']}")
            return {"ok": False, "error": result["error"]}

        readme_url = result.get("readme_url", "")
        logger.info(f"✅ README generation complete! 🌐 URL: {readme_url}")
        return {"ok": True, "readme_url": readme_url}

    except Exception as e:
        logger.exception("❌ Error processing webhook")
        return {"ok": False, "error": str(e)}
