from abc import ABC, abstractmethod
from pathlib import Path

class Cloner(ABC):
    @abstractmethod
    def clone(self, directory: Path):
        pass
