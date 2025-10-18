import os
import json
import logging
import requests
from langchain_core.tools import tool

# ---------------- Logging setup (Azure-friendly) ----------------
logging.basicConfig(
    level=logging.INFO,  # INFO level shows all useful details in Azure Logs
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("github_api_tool")

#  API request / tool call to GitHub to fetch the content changes in each file between two commits 

@tool
def fetch_commit_diffs(owner: str, repo: str, base_sha: str, head_sha: str) -> dict:
    """
    Fetch the content differences between two commits on GitHub.

    Args:
        owner (str): GitHub username or org
        repo (str): Repository name
        base_sha (str): Older commit SHA
        head_sha (str): Newer commit SHA

    Returns:
        dict: JSON object containing diff details for each changed file
    """

    try:
       
        # Read GitHub token from environment
       
        token = os.getenv("TOKEN_GITHUB") or os.getenv("GITHUB_TOKEN")
        if not token:
            logger.error("❌ Missing GitHub token (TOKEN_GITHUB or GITHUB_TOKEN).")
            return {"error": "Missing GitHub token in environment variables"}

      
        #  Prepare GitHub API request
       
        url = f"https://api.github.com/repos/{owner}/{repo}/compare/{base_sha}...{head_sha}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {token}",
        }

        logger.info(f"🔍 Fetching diff between {base_sha[:7]} → {head_sha[:7]} for {owner}/{repo}")
        response = requests.get(url, headers=headers)

        
        # Handle API errors
      
        if response.status_code != 200:
            logger.warning(
                f"⚠️ GitHub API responded with {response.status_code}: {response.text[:200]}"
            )
            return {"error": response.text, "status": response.status_code}

        data = response.json()
        files = data.get("files", [])
        logger.info(f"📁 {len(files)} files changed between commits.")

     
        # 🧩 Extract file diff details
        changes_summary = []
        for f in files:
            file_info = {
                "filename": f.get("filename"),
                "status": f.get("status"),
                "additions": f.get("additions"),
                "deletions": f.get("deletions"),
                "changes": f.get("changes"),
                "patch": f.get("patch", ""),  # actual diff
            }
            changes_summary.append(file_info)

        output = {
            "base_commit": base_sha,
            "head_commit": head_sha,
            "total_files_changed": len(files),
            "files": changes_summary,
        }

    
        # 💾 Save diff to disk (for agents)
        os.makedirs("data", exist_ok=True)
        output_path = os.path.join("data", "commit_diff.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        logger.info(f"✅ Diff details saved successfully → {output_path}")
        return output

    except Exception as e:
        logger.exception(f"❌ Exception occurred while fetching commit diffs: {e}")
        return {"error": str(e)}
