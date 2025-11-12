import requests
import urllib.parse

from .pull_request import PullRequest, PRStatus
from .vcs_instance import VcsInstance

class GitlabInstance(VcsInstance):
    def __init__(self, token: str, base_url: str):
        super().__init__(token, base_url)
    
    def _headers(self) -> dict[str, str]:
        return {"Private-Token": self.token}
    
    def validate_connection(self) -> bool:
        try:
            url = f"{self.base_url}/api/v4/user"
            r = requests.get(url, headers=self._headers(), timeout=5)
            r.raise_for_status()
            return True
        except requests.RequestException:
            return False
    
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