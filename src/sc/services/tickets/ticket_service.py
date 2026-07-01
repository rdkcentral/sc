# Copyright 2025 RDK Management
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from functools import cached_property
import re
import logging

from .exceptions import TicketIdentifierNotFound
from sc.prompter import Prompter
from .ticket import Ticket
from .ticket_config import TicketHostConfig, TicketHostModel
from .ticketing_instances.ticket_instance_factory import TicketingInstanceFactory
from .ticketing_instances.ticketing_instance import TicketingInstance

logger = logging.getLogger(__name__)

class TicketService:
    def __init__(
            self,
            config: TicketHostConfig | None = None,
            factory: TicketingInstanceFactory | None = None,
            prompter: Prompter | None = None
            ):
        self._config = config or TicketHostConfig()
        self._factory = factory or TicketingInstanceFactory()
        self._prompter = prompter or Prompter()

    def get_identifiers(self) -> set[str]:
        """Return all configured ticeting instance identifiers."""
        return self._config.get_identifiers()

    def get_ticket(self, identifier: str, ticket_num: str) -> Ticket:
        """Match an instance identifier and ticket num to a ticket instance and ticket."""
        cfg = self._config.get(identifier)
        instance = self._create_instance(cfg)

        ticket_id = f"{cfg.project_prefix or ''}{ticket_num}"
        return instance.read_ticket(ticket_id)

    def get_ticket_from_branch(self, branch_name: str) -> Ticket:
        """Match the branch to a ticket and return said ticket.

        Args:
            branch_name (str): The current branch name.

        Raises:
            TicketIdentifierNotFound: Raised when the branch doesn't match any
                identifiers in the ticket host config.
        """
        identifier, ticket_num = self.get_ref_from_branch(branch_name)
        return self.get_ticket(identifier, ticket_num)

    def prompt_ticket(self) -> Ticket:
        """Prompt the user to select a ticket and return it."""
        ticket_conf = self._config.get_config()
        logger.info("Please enter the prefix of the ticket instance:")
        logger.info("PREFIX --- INSTANCE URL --- DESCRIPTION")
        for id, conf in ticket_conf.items():
            logger.info(f"{id} --- {conf.url} --- {conf.description or ''}")

        while True:
            identifier = self._prompter.ask("Prefix")
            if identifier in ticket_conf:
                break
            logger.info(f"Prefix {identifier} not found in instances")

        ticket_num = self._prompter.ask("Ticket number")

        return self.get_ticket(identifier, ticket_num)

    def get_ref_from_branch(self, branch_name: str) -> tuple[str, str]:
        pattern = self._branch_id_pattern
        if m := pattern.search(branch_name):
            identifier = m.group(1)
            ticket_num = m.group(2)
            return identifier, ticket_num
        raise TicketIdentifierNotFound(
            f"Branch {branch_name} doesn't match any ticketing instances! "
            f"Found instances {', '.join(self._config.get_identifiers())}")

    @cached_property
    def _branch_id_pattern(self) -> re.Pattern:
        host_identifiers = self._config.get_identifiers()
        identifiers_pattern = "|".join(map(re.escape, host_identifiers))
        return re.compile(
            fr'(?:^|/)({identifiers_pattern})[-_]?(\d+)',
            re.IGNORECASE
        )

    def _create_instance(self, cfg: TicketHostModel) -> TicketingInstance:
        return self._factory.create(
            provider=cfg.provider,
            url=cfg.url,
            token=cfg.api_key,
            auth_type=cfg.auth_type,
            username=cfg.username,
            cert=cfg.cert
        )
