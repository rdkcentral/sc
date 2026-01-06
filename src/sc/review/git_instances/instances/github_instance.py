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

from sc.review.code_review import CRStatus, CodeReview
from ..git_instance import GitInstance

class GithubInstance(GitInstance):
    def __init__(self, token: str, base_url: str | None):
        super().__init__(token, base_url or "https://api.github.com")

    def _headers(self) -> dict:
        return {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {self._token}"
        }

    def validate_connection(self) -> bool:
        url = f"{self.base_url}/user"
        try:
            r = requests.get(url, headers=self._headers(), timeout=10)
            r.raise_for_status()
            return True
        except requests.exceptions.Timeout as e:
            raise ConnectionError("GitHub API request timed out.") from e
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            if status in (401, 403):
                raise ConnectionError("Invalid GitHub token.") from e
            raise ConnectionError(f"GitHub API error: {status}") from e
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError("Network connection to GitHub failed.") from e

    def get_code_review(self, repo: str, source_branch: str) -> CodeReview | None:
        """Get information about a code review.

        Args:
            repo (str): An identifier for the repo e.g. org/repo
            source_branch (str): The source branch of review.

        Raises:
            RuntimeError: If an error occurs.

        Returns:
            CodeReview | None: An object describing a code review.
        """
        url = f"{self.base_url}/repos/{repo}/pulls"
        owner = repo.split("/")[0]
        params = {"state": "all", "head": f"{owner}:{source_branch}"}

        try:
            r = requests.get(url, headers=self._headers(), params=params, timeout=10)
            r.raise_for_status()
            prs = r.json()
        except requests.Timeout as e:
            raise RuntimeError("GitHub request timed out") from e
        except requests.HTTPError as e:
            raise RuntimeError(
                f"GitHub API error {e.response.status_code}: {e.response.text}"
            ) from e
        except ValueError as e:  # JSON decode error
            raise RuntimeError("Invalid JSON from GitHub API") from e
        except requests.RequestException as e:
            raise RuntimeError("GitHub request failed") from e

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
