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
from collections.abc import Iterable

from .models import CodeReview
from .exceptions import RemoteUrlNotFound
from .git_flow_branch_strategy import GitFlowBranchStrategy
from .git_instances import GitFactory, GitInstance
from .models import RepoInfo
from .review_config import GitHostConfig

class GitHostService:
    def __init__(
            self,
            git_config: GitHostConfig | None = None,
            factory: GitFactory | None = None,
            branch_strategy: GitFlowBranchStrategy | None = None
        ):
        self._git_config = git_config or GitHostConfig()
        self._factory = factory or GitFactory()
        self._branch_strategy = branch_strategy or GitFlowBranchStrategy()

    def get_git_review_data(self, repo_info: RepoInfo) -> CodeReview | None:
        git_instance = self._create_git_instance(repo_info.remote_url)
        return git_instance.get_code_review(repo_info.repo_slug, repo_info.branch)

    def get_create_cr_url(
        self,
        repo_info: RepoInfo,
    ) -> str:
        git_instance = self._create_git_instance(repo_info.remote_url)
        target_branch = self._branch_strategy.get_target_branch(
            repo_info.directory, repo_info.branch)
        return git_instance.get_create_cr_url(repo_info.repo_slug, repo_info.branch, target_branch)

    def _create_git_instance(self, remote_url: str) -> GitInstance:
        remote_pattern = _match_remote_pattern(
            remote_url, self._git_config.get_patterns())
        git_data = self._git_config.get(remote_pattern)
        return self._factory.create(
            git_data.provider,
            token=git_data.token,
            base_url=git_data.url
        )

def _match_remote_pattern(remote_url: str, url_patterns: Iterable[str]) -> str:
    """Match the remote url to a pattern in the git instance config.

    Args:
        remote_url (str): The remote url of the git repository.
        url_patterns (Iterable[str]): An iterable of patterns to check against.

    Raises:
        RemoteUrlNotFound: Raised when the remote url matches no patterns.

    Returns:
        str: The matched pattern.
    """
    for pattern in url_patterns:
        if pattern in remote_url:
            return pattern
    raise RemoteUrlNotFound(f"{remote_url} doesn't match any patterns! \n"
                            f"Remote patterns found: {', '.join(url_patterns)}")
