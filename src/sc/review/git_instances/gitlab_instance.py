import requests
import urllib.parse

from .pull_request import PullRequest, PRStatus
from .git_instance import GitInstance

class GitlabInstance(GitInstance):
    def __init__(self, token: str, base_url: str):
        super().__init__(token, base_url)
    
    def _headers(self) -> dict[str, str]:
        return {"Private-Token": self.token}
    
    def validate_connection(self) -> bool:
        url = f"{self.base_url}/api/v4/user"
        try:
            r = requests.get(url, headers=self._headers(), timeout=10)
            if r.status_code == 401 or r.status_code == 403:
                raise ConnectionError("Invalid GitLab token or insufficient permissions.")
            elif r.status_code >= 400:
                raise ConnectionError(f"GitLab API error: {r.status_code}")
            return True
        except requests.exceptions.Timeout as e:
            raise ConnectionError("GitLab API request timed out.") from e
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError("Network connection to GitLab failed.") from e

    
    def get_pull_request(self, repo: str, source_branch: str) -> PullRequest:
        safe_repo = urllib.parse.quote(repo, safe='')
        url = f"{self.base_url}/api/v4/projects/{safe_repo}/merge_requests"
        params = {"state": "all", "source_branch": source_branch}
        r = requests.get(url, headers=self._headers(), params=params, timeout=10)
        r.raise_for_status()
        prs = r.json()
        if not prs:
            return None
        pr = prs[0]

        state = pr["state"]
        if state == "merged":
            status = PRStatus.MERGED
        elif state == "opened":
            status = PRStatus.OPEN
        else:
            status = PRStatus.CLOSED

        return PullRequest(url=pr["web_url"], status=status)
    
    def get_create_pr_url(self, repo, source_branch, target_branch = "develop"):
        safe_repo = urllib.parse.quote(repo, safe="")
        params = {
            "merge_request[source_branch]": source_branch,
            "merge_request[target_branch]": target_branch,
        }
        query = urllib.parse.urlencode(params)
        return f"{self.base_url}/{safe_repo}/-/merge_requests/new?{query}"