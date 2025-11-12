from sc.review.exceptions import TicketIdentifierNotFound
from .jira_instance import JiraInstance
from .redmine_instance import RedmineInstance
from .ticketing_instance import TicketingInstance

class TicketingInstanceFactory:
    _registry = {
        "redmine": RedmineInstance,
        "jira": JiraInstance
    }

    @classmethod
    def providers(cls) -> list[str]:
        return list(cls._registry.keys())

    @classmethod
    def create(
        cls,
        provider: str,
        url: str,
        token: str,
    ) -> TicketingInstance:
        try:
            return cls._registry[provider](url=url, password=token)
        except KeyError:
            raise TicketIdentifierNotFound(
                f"Provider {provider} doesn't match any ticketing instance!")
