from abc import ABC, abstractmethod

from .pull_request import PullRequest

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
    def get_pull_request(self, repo: str, source_branch: str) -> PullRequest:
        pass

    @abstractmethod
    def get_create_pr_url(
        self, 
        repo: str, 
        source_branch: str, 
        target_branch: str = "develop"
    ):
        pass