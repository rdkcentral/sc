
from .github_instance import GithubInstance
from .gitlab_instance import GitlabInstance
from .git_instance import GitInstance

class GitFactory:
    _registry = {
        "github": GithubInstance,
        "gitlab": GitlabInstance
    }

    @classmethod
    def names(cls) -> list[str]:
        return list(cls._registry.keys())

    @classmethod
    def create(cls, name: str, token: str, base_url: str | None) -> GitInstance:
        try:
            return cls._registry[name.lower()](token=token, base_url=base_url)
        except KeyError:
            raise ValueError(f"Provider name {name} doesn't match any VCS instance!")