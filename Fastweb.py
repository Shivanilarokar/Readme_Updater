from fastapi import FastAPI, Request
import logging, sys, json, os
from Readme_Updater_agent import generate_updated_readme 
from githubapitoolcall import fetch_commit_diffs

# ---------------- Logging setup (Azure-friendly) ----------------
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger("main")

# ---------------- FastAPI app ----------------
app = FastAPI()

# basic health check endpoint
@app.get("/")
def home():
    """Simple health check endpoint."""
    logger.info("🚀 Health check passed")
    return {"message": "Hello from FastAPI Webhook!"}


# webhook endpoint to receive GitHub push events
@app.post("/webhook")
async def webhook(request: Request):
    """Receives JSON payload from GitHub push event."""
    try:
        payload = await request.json()

        # Log high-level info
        delivery_id = request.headers.get("X-GitHub-Delivery", "unknown")
        event_type = request.headers.get("X-GitHub-Event", "push")

        repo = payload["repository"]["full_name"]
        pusher = payload["pusher"]["name"]
        branch_ref = payload.get("ref", "")
        branch = branch_ref.split("/")[-1] if branch_ref else "unknown"

        logger.info(f"📦 New webhook delivery: {delivery_id}")
        logger.info(f"🔔 Event type: {event_type}")
        logger.info(f"📁 Repository: {repo}")
        logger.info(f"👤 Pushed by: {pusher} to branch: {branch}")

        commits = payload.get("commits", [])
        logger.info(f"🧩 Total commits: {len(commits)}")

        all_changed_files = []
        for commit in commits:
            commit_id = commit.get("id", "")[:7]
            author = commit.get("author", {}).get("name", "unknown")
            message = commit.get("message", "")
            added = commit.get("added", [])
            modified = commit.get("modified", [])
            removed = commit.get("removed", [])

            commit_info = {
                "commit_id": commit_id,
                "message": message,
                "author": author,
                "added": added,
                "modified": modified,
                "removed": removed,
            }

            logger.info(json.dumps(commit_info, indent=2))
            all_changed_files.extend(added + modified + removed)

        logger.info(f"🗂️ Changed files ({len(all_changed_files)}): {all_changed_files}")

        # ✅ Trigger README generator only if relevant files changed
        if any(fname.endswith((".py", ".ipynb", "README.md")) for fname in all_changed_files):
            logger.info("🤖 Triggering README generator agent...")
            try:
                # Extract commit SHAs for diff comparison
                base_sha = payload.get("before", "")
                head_sha = payload.get("after", "")
                
                # Parse repository name
                repo_parts = repo.split("/")
                owner = repo_parts[0]
                repo_name = repo_parts[1]
                
                logger.info(f"🔍 Fetching detailed diff data from GitHub API...")
                logger.info(f"🔍 Repository: {owner}/{repo_name}")
                logger.info(f"🔍 Base SHA: {base_sha}")
                logger.info(f"🔍 Head SHA: {head_sha}")
                
                # 🟢 NEW: Fetch actual diff data from GitHub API
                diff_data = fetch_commit_diffs.invoke({
                    "owner"=owner,
                    "repo":repo_name,
                    "base_sha":base_sha,
                    "head_sha":head_sha
                })
                
                if "error" in diff_data:
                    logger.error(f"❌ Error fetching diff data: {diff_data['error']}")
                    return {"ok": False, "error": f"Failed to fetch diff data: {diff_data['error']}"}
                
                logger.info(f"✅ Successfully fetched diff data for {diff_data.get('total_files_changed', 0)} files")
                
                # 🟢 Enhanced: pass actual diff data for accurate analysis
                state = {
                    "repo": repo_name,
                    "owner": owner,
                    "branch": branch,
                    "base_sha": base_sha,
                    "head_sha": head_sha,
                    "total_files_changed": diff_data.get("total_files_changed", 0),
                    "files": diff_data.get("files", []),  # Actual diff data from GitHub API
                    "messages": [commit.get("message", "") for commit in commits],
                    "commit_details": commits,  # Full commit details
                    "pusher": pusher,
                    "repository_url": payload.get("repository", {}).get("html_url", ""),
                    "compare_url": payload.get("compare", "")
                }
                
                logger.info(f"🔍 State with diff data: {len(state['files'])} files with actual changes")

                output = generate_updated_readme(state)
                logger.info("✅ README generation completed successfully.")
                logger.info(f"📝 Generated README preview:\n{str(output)[:500]}")  # log first few lines
            except Exception as agent_err:
                logger.exception("⚠️ Error running README generator agent")
        else:
            logger.info("ℹ️ No relevant files changed — skipping README generation.")

        return {"ok": True, "total_commits": len(commits)}

    except Exception as e:
        logger.exception("❌ Error processing webhook")
        return {"ok": False, "error": str(e)}
