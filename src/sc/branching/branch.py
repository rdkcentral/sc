from dataclasses import dataclass
from enum import Enum

# This is exactly StrEnum which was released in Py3.11 but we are supporting 3.10+
class BranchType(str, Enum):
    FEATURE = "feature"
    RELEASE = "release"
    SUPPORT = "support"
    HOTFIX = "hotfix"
    DEVELOP = "develop"
    MASTER = "master"

    def __str__(self):
        return self.value

@dataclass
class Branch:
    type: BranchType
    suffix: str = None

    def __post_init__(self):
        if not self.suffix and not self._is_primary_branch:
            raise ValueError("Can't create non primary branch with no suffix.")
    
    @property
    def name(self) -> str:
        if self.suffix:
            return f"{self.type}/{self.suffix}"
        return str(self.type)
        
    def _is_primary_branch(self) -> bool:
        return self.type in {BranchType.DEVELOP, BranchType.MASTER}
