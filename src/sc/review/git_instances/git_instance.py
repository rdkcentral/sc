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

from abc import ABC, abstractmethod

from ..code_review import CodeReview

class GitInstance(ABC):
    def __init__(self, token: str, base_url: str | None):
        self._token = token
        self.base_url = base_url.rstrip("/") if base_url else None

    @abstractmethod
    def validate_connection(self) -> bool:
        """Abstract Method:
        Validates if connection to the git instance is successful.

        Raises:
            ConnectionError: If the connection is unsuccessful.

        Returns:
            bool: True if connection is successful.
        """
        pass

    @abstractmethod
    def get_code_review(self, repo: str, source_branch: str) -> CodeReview:
        """Get information about a branches code review.

        Args:
            repo (str): An identifier of the repo in the instance e.g "org/repo".
            source_branch (str): The branch the code review is made from.

        Returns:
            CodeReview: dataclass with information about the code review.
        """
        pass

    @abstractmethod
    def get_create_cr_url(
        self,
        repo: str,
        source_branch: str,
        target_branch: str = "develop"
    ) -> str:
        """Get the URL to create a code review for a repo and branch.

        Args:
            repo (str): An identifier of the repo in the instance e.g "org/repo".
            source_branch (str): The branch the code review will be made from.
            target_branch (str, optional): The branch the code review will
                merge into. Defaults to "develop".

        Returns:
            str: The URL to create a code review.
        """
        pass
