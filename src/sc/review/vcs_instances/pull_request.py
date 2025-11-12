from dataclasses import dataclass
from enum import Enum

class PRStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"

@dataclass
class PullRequest:
    url: str
    status: PRStatus