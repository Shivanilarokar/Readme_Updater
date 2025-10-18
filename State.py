# state.py

from typing import TypedDict, List, Dict, Any, Optional

class RepoState(TypedDict):
    """
    Enhanced data structure for the AutoDoc Agent.
    Contains all necessary information for README generation and GitHub operations.
    """

    # Repository Information
    repo: str                    # e.g. "DSA-Questions-"
    owner: str                   # e.g. "Shivanilarokar"
    branch: str                  # branch name (e.g. "master")
    
    # Commit Information
    base_sha: str                # base commit SHA
    head_sha: str                # head commit SHA
    
    # Change Information
    total_files_changed: int     # number of files changed
    files: List[Dict[str, Any]]  # detailed diff data from GitHub API
    
    # Commit Details
    messages: List[str]          # commit messages
    commit_details: List[Dict[str, Any]]  # full commit details
    pusher: str                  # who pushed the changes
    
    # Repository URLs
    repository_url: str          # GitHub repository URL
    compare_url: str             # GitHub compare URL
    
    # Agent State
    messages: List[Dict[str, Any]]  # LLM messages or tool outputs
    
    # Results (populated after processing)
    branch_success: Optional[bool]  # whether branch creation succeeded
    branch_name: Optional[str]     # name of created branch
    pr_success: Optional[bool]     # whether PR creation succeeded
    pr_url: Optional[str]          # URL of created PR
    pr_number: Optional[int]       # PR number
