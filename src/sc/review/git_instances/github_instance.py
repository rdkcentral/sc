import requests

from ..core.code_review import CRStatus, CodeReview
from ..core.git_instance import GitInstance

class GithubInstance(GitInstance):
    def __init__(self, token: str, base_url: str | None):
        super().__init__(token, base_url or "https://api.github.com")

    def _headers(self) -> dict:
        return {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {self.token}"
        }

    def validate_connection(self) -> bool:
        url = f"{self.base_url}/user"
        try:
            r = requests.get(url, headers=self._headers(), timeout=10)
            if r.status_code == 401:
                raise ConnectionError("Invalid GitHub token.")
            elif r.status_code >= 400:
                raise ConnectionError(f"GitHub API error: {r.status_code}")
            return True
        except requests.exceptions.Timeout as e:
            raise ConnectionError("GitHub API request timed out.") from e
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError("Network connection to GitHub failed.") from e

    def get_code_review(self, repo: str, source_branch: str) -> CodeReview | None:
        url = f"{self.base_url}/repos/{repo}/pulls"
        owner = repo.split("/")[0]
        params = {"state": "all", "head": f"{owner}:{source_branch}"}
        r = requests.get(url, headers=self._headers(), params=params, timeout=10)
        r.raise_for_status()
        prs = r.json()
        if not prs:
            return None
        pr = prs[0]
        # GitHub marks merged PRs as state="closed", merged=True
        if pr.get("merged"):
            status = CRStatus.MERGED
        elif pr["state"] == "open":
            status = CRStatus.OPEN
        else:
            status = CRStatus.CLOSED

        return CodeReview(url=pr["html_url"], status=status)

    def get_create_cr_url(
        self,
        repo: str,
        source_branch: str,
        target_branch: str = "develop"
    ) -> str:
        return f"https://github.com/{repo}/compare/{target_branch}...{source_branch}"