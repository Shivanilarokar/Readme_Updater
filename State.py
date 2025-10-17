# state.py
from typing import TypedDict, List, Dict, Any

class RepoState(TypedDict):
    """
    Defines the data structure shared across nodes in the LangGraph.
    Compatible with fetch_commit_diffs output.
    """

    repo: str                    # e.g. "shivani/ai-readme-updater"
    base_sha: str                # base commit SHA
    head_sha: str                # head commit SHA
    total_files_changed: int     # number of files changed
    files: List[Dict[str, Any]]  # each file's diff details
    messages: List[Dict[str, Any]]  # LLM messages or tool outputs
