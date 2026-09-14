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

from github import Github, BadCredentialsException, UnknownObjectException

from sc.review.models import CRStatus, CodeReview
from ..git_instance import GitInstance

class GithubInstance(GitInstance):
    def __init__(self, token: str, base_url: str | None):
        super().__init__(token, base_url or "https://api.github.com")
        self._gh = Github(self._token, base_url=self.base_url, timeout=10)

    def validate_connection(self) -> bool:
        try:
            # Strangely it's only when you try to use the user object,
            # that the exception is thrown
            self._gh.get_user().id
        except BadCredentialsException as e:
            raise ConnectionError("Invalid Github credentials") from e
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError("Network connection to GitHub failed.") from e
        return True

    def get_code_review(
            self, repo: str, source_branch: str, target_branch: str) -> CodeReview:
        """Get information about a code review.

        Args:
            repo (str): An identifier for the repo e.g. org/repo
            source_branch (str): The source branch of review.
            target_branch (str): The target branch of the review.

        Raises:
            RuntimeError: If an error occurs.

        Returns:
            CodeReview: An object describing a code review.
        """
        try:
            gh_repo = self._gh.get_repo(f'{repo}')
            matching_prs = gh_repo.get_pulls(state="all", head=f"{gh_repo.owner.login}:{source_branch}")
        except BadCredentialsException as e:
            raise RuntimeError("Invalid Github credentials") from e
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError("Github request failed") from e
        except UnknownObjectException as e:
            data = e.data or {}
            status = data.get("status", e.status)
            message = data.get("message", e.message)
            raise RuntimeError(f"Github API error {status}: {message}") from e

        if matching_prs.totalCount == 0:
            create_cr_url = self._get_create_cr_url(repo, source_branch, target_branch)
            return CodeReview(url=None, status=None, create_url=create_cr_url)

        pr = matching_prs[0]
        # GitHub marks merged PRs as state="closed", merged=True
        if pr.merged:
            status = CRStatus.MERGED
        elif pr.state == "open":
            status = CRStatus.OPEN
        else:
            status = CRStatus.CLOSED

        return CodeReview(url=pr.html_url, status=status)

    def _get_create_cr_url(
        self,
        repo: str,
        source_branch: str,
        target_branch: str = "develop"
    ) -> str:
        return f"https://github.com/{repo}/compare/{target_branch}...{source_branch}"
