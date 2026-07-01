from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from sc.config_manager import ConfigManager
from sc.exceptions import ConfigError

class TicketHostModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

    url: str
    provider: str
    api_key: str
    username: str | None = None
    auth_type: Literal["token", "basic"] = "token"
    project_prefix: str | None = None
    description: str | None = None
    cert: str | None = None

class TicketHostConfig:
    def __init__(self):
        self._ticket_config = ConfigManager('ticketing_instances')

    def get_config(self) -> dict[str, TicketHostModel]:
        """Return all ticketing instance configs keyed by identifier."""
        return {k: TicketHostModel(**v) for k,v in self._ticket_config.get_config().items()}

    def get_identifiers(self) -> set[str]:
        """Return all configured ticketing instance identifiers."""
        return set(self._ticket_config.get_config().keys())

    def get(self, identifier: str) -> TicketHostModel:
        """Return the ticketing config for a specific identifier."""
        lookup = {k.lower(): k for k in self.get_identifiers()}
        data = self._ticket_config.get_config().get(lookup.get(identifier.lower()))
        if not data:
            raise ConfigError(
                f"Ticket instance config doesn't contain entry for {identifier}")
        try:
            return TicketHostModel(**data)
        except ValidationError as e:
            raise ConfigError(f"Invalid config for ticketing instance {identifier}: {e}")

    def write(self, branch_prefix: str, ticket_data: TicketHostModel):
        """Persist ticketing config for a branch prefix."""
        self._ticket_config.update_config(
            {branch_prefix: ticket_data.model_dump(exclude_none=True)})

