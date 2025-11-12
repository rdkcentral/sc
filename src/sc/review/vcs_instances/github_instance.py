import requests

from .pull_request import PRStatus, PullRequest
from .vcs_instance import VcsInstance

class GithubInstance(VcsInstance):
    def __init__(self, token: str, base_url: str | None):
        super().__init__(token, base_url or "https://api.github.com")

    def _headers(self) -> dict:
        return {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {self.token}"
        }
    
    def get_pull_request(self, repo: str, source_branch: str) -> PullRequest | None:
        url = f"{self.base_url}/repos/{repo}/pulls"
        params = {"state": "all", "head": f"{repo}:{source_branch}"}
        r = requests.get(url, headers=self._headers(), params=params, timeout=10)
        r.raise_for_status()
        prs = r.json()
        if not prs:
            return None
        pr = prs[0]
        # GitHub marks merged PRs as state="closed", merged=True
        if pr.get("merged"):
            status = PRStatus.MERGED
        elif pr["state"] == "open":
            status = PRStatus.OPEN
        else:
            status = PRStatus.CLOSED

        return PullRequest(url=pr["html_url"], status=status)

    def get_create_pr_url(
        self, 
        repo: str, 
        source_branch: str, 
        target_branch: str = "develop"
    ) -> str:
        return f"https://github.com/{repo}/compare/{target_branch}...{source_branch}"