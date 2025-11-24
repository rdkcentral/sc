from sc.review.exceptions import TicketIdentifierNotFound
from ..ticketing_instances import JiraInstance, RedmineInstance
from ..core.ticketing_instance import TicketingInstance

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
        cert: str | None = None
    ) -> TicketingInstance:
        try:
            return cls._registry[provider](url=url, password=token, cert=cert)
        except KeyError:
            raise TicketIdentifierNotFound(
                f"Provider {provider} doesn't match any ticketing instance!")
