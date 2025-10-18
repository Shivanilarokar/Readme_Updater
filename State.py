from typing import TypedDict, List, Dict, Any, Optional

class RepoState(TypedDict):
    """
    Core data structure for the Auto README Agent.
    It holds everything needed from the webhook payload and the diff-fetching github api tool call
    """

    # Repository Information
    repo: str                    # e.g. "Readme_Updater"
    owner: str                   # e.g. "Shivanilarokar"
    branch: str                  # e.g. "main" or "master"
    
    # Commit Information
    base_sha: str                # base commit SHA (from webhook 'before')
    head_sha: str                # head commit SHA (from webhook 'after')
    pusher: str                  # name of the person who pushed
    
    # Change Information
    total_files_changed: int     # number of files changed
    files: List[Dict[str, Any]]  # detailed diff data from GitHub Compare API tool
    
    # Commit Details
    commit_messages: List[str]   # commit messages from webhook
    commit_details: List[Dict[str, Any]]  # optional detailed commit info if needed
    
    # Repository URLs
    repository_url: str          # repo HTML URL
    compare_url: str             # compare URL between commits

     
    # Output (result)
    readme_url: Optional[str]    # final README.md URL after update
