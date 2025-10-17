# readme_updateragent.py

import os
import json
import logging
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END

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
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.6,
)

# ---------------- Node Logic ----------------
def generate_updated_readme(state: RepoState):
    """
    Node that fetches diffs (if needed) and generates README using LLM.
    """
    try:
        logger.info("🚀 Starting README update agent...")

        # If no diff data is provided in state, fetch it
        if not state.get("files"):
            logger.info("🔍 No diff data found in state — calling fetch_commit_diffs...")
            diff_data = fetch_commit_diffs(
                owner="shivanilarokar",
                repo=state["repo"],
                base_sha=state["base_sha"],
                head_sha=state["head_sha"],
            )

            if "error" in diff_data:
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
        response = llm.invoke(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
        )

        readme_text = response.content.strip()

        os.makedirs("data", exist_ok=True)
        output_path = os.path.join("data", "UPDATED_README.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(readme_text)

        logger.info(f"✅ README saved successfully → {output_path}")

        # Update messages in state
        return {
            "repo": state["repo"],
            "base_sha": state["base_sha"],
            "head_sha": state["head_sha"],
            "total_files_changed": state["total_files_changed"],
            "files": state["files"],
            "messages": [{"role": "assistant", "content": readme_text}],
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
