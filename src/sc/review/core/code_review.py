from dataclasses import dataclass
from enum import Enum

class CRStatus(str, Enum):
    OPEN = "Open"
    CLOSED = "Closed"
    MERGED = "Merged"

    def __str__(self):
        return self.value

@dataclass
class CodeReview:
    url: str
    status: CRStatus