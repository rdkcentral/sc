import re

from .exceptions import TicketIdentifierNotFound
from .models import Ticket
from .review_config import ReviewConfig
from .ticketing_instances import TicketingInstance, TicketingInstanceFactory

class TicketService:
    def __init__(
            self,
            config: ReviewConfig | None = None,
            factory: TicketingInstanceFactory | None = None,
            ):
        self._config = config if config else ReviewConfig()
        self._factory = factory if factory else TicketingInstanceFactory()

    def resolve(
            self, identifier: str, ticket_num: str) -> tuple[TicketingInstance, Ticket]:
        cfg = self._config.get_ticket_host_data(identifier)
        instance = self._factory.create(
            provider=cfg.provider,
            url=cfg.url,
            token=cfg.api_key,
            auth_type=cfg.auth_type,
            username=cfg.username,
            cert=cfg.cert
        )
        ticket_id = f"{cfg.project_prefix or ''}{ticket_num}"
        ticket = instance.read_ticket(ticket_id)

        return instance, ticket

    def update(self, instance: TicketingInstance, ticket_id: str, comment: str):
        instance.add_comment_to_ticket(ticket_id, comment)

    def match_branch(self, branch_name: str) -> tuple[str, str]:
        """Match the branch to an identifier in the config.

        Args:
            branch_name (str): The current branch name.

        Raises:
            TicketIdentifierNotFound: Raised when the branch doesn't match any
                identifiers in the ticket host config.

        Returns:
            tuple[str, str]: (matched_identifier, ticket_number)
        """
        host_identifiers = self._config.get_ticket_host_identifiers()
        for identifier in host_identifiers:
            # Matches the identifier, followed by - or _, followed by a number
            if m := re.search(fr'{identifier}[-_]?(\d+)', branch_name):
                ticket_num = m.group(1)
                return identifier, ticket_num
        raise TicketIdentifierNotFound(
            f"Branch {branch_name} doesn't match any ticketing instances! "
            f"Found instances {', '.join(host_identifiers)}")
