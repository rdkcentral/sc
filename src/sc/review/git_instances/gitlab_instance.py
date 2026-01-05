# Copyright 2025 RDK Management
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import requests
import urllib.parse

from ..code_review import CodeReview, CRStatus
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
            r.raise_for_status()
            return True
        except requests.exceptions.Timeout as e:
            raise ConnectionError("GitLab API request timed out.") from e
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            if status == 401 or status == 403:
                raise ConnectionError(
                    "Invalid GitLab token or insufficient permissions.") from e
            raise ConnectionError(f"GitLab API error: {status}") from e
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError("Network connection to GitLab failed.") from e

    def get_code_review(self, repo: str, source_branch: str) -> CodeReview:
        safe_repo = urllib.parse.quote(repo, safe='')
        url = f"{self.base_url}/api/v4/projects/{safe_repo}/merge_requests"
        params = {"state": "all", "source_branch": source_branch}
        try:
            r = requests.get(url, headers=self._headers(), params=params, timeout=10)
            r.raise_for_status()
            prs = r.json()
        except requests.Timeout as e:
            raise RuntimeError("Gitlab request timed out") from e
        except requests.HTTPError as e:
            raise RuntimeError(
                f"Gitlab API error {r.status_code}: {r.text}"
            ) from e
        except ValueError as e: # JSON decode error
            raise RuntimeError("Invalid JSON from Gitlab API") from e
        except requests.RequestException as e:
            raise RuntimeError("Gitlab request failed") from e

        if not prs:
            return None
        pr = prs[0]

        state = pr["state"]
        if state == "merged":
            status = CRStatus.MERGED
        elif state == "opened":
            status = CRStatus.OPEN
        else:
            status = CRStatus.CLOSED

        return CodeReview(url=pr["web_url"], status=status)

    def get_create_cr_url(
            self,
            repo: str,
            source_branch: str,
            target_branch: str="develop"
        ):
        params = {
            "merge_request[source_branch]": source_branch,
            "merge_request[target_branch]": target_branch,
        }
        query = urllib.parse.urlencode(params)
        return f"{self.base_url}/{repo}/-/merge_requests/new?{query}"
