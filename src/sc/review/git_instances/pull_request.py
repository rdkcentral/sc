from dataclasses import dataclass
from enum import Enum

class PRStatus(str, Enum):
    OPEN = "Open"
    CLOSED = "Closed"
    MERGED = "Merged"

    def __str__(self):
        return self.value

@dataclass
class PullRequest:
    url: str
    status: PRStatus