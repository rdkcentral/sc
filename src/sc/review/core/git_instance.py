from abc import ABC, abstractmethod

from .code_review import CodeReview

class GitInstance(ABC):
    @abstractmethod
    def __init__(self, token: str, base_url: str | None):
        self.token = token
        self.base_url = base_url.rstrip("/") if base_url else None

    @abstractmethod
    def validate_connection(self) -> bool:
        """Abstract Method:
        Validates if connection to the git instance is successful.

        Raises:
            ConnectionError: If the connection is unsuccesful.

        Returns:
            bool: True if connection is successful.
        """
        pass

    @abstractmethod
    def get_code_review(self, repo: str, source_branch: str) -> CodeReview:
        pass

    @abstractmethod
    def get_create_cr_url(
        self,
        repo: str,
        source_branch: str,
        target_branch: str = "develop"
    ) -> str:
        pass