from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from sc.config_manager import ConfigManager, MergePolicy
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
    """Manage ``ticketing_instances`` in the shared review tool configuration."""

    def __init__(self, config_manager: ConfigManager | None = None):
        self._config_manager = config_manager or ConfigManager(
            "review",
            merge_policy={"ticketing_instances": MergePolicy.PREFER_ADMIN},
        )

    def _get_config(self) -> dict:
        return self._config_manager.get_config().get("ticketing_instances", {})

    def get_config(self) -> dict[str, TicketHostModel]:
        """Return all ticketing instance configs keyed by identifier."""
        result: dict[str, TicketHostModel] = {}
        for k, v in self._get_config().items():
            try:
                result[k] = TicketHostModel(**v)
            except ValidationError as e:
                raise ConfigError(f"Invalid config for ticketing instance {k}: {e}") from e
        return result

    def get_identifiers(self) -> set[str]:
        """Return all configured ticketing instance identifiers."""
        return set(self._get_config().keys())

    def get(self, identifier: str) -> TicketHostModel:
        """Return the ticketing config for a specific identifier."""
        lookup = {k.lower(): k for k in self.get_identifiers()}
        data = self._get_config().get(lookup.get(identifier.lower()))
        if not data:
            raise ConfigError(
                f"Ticket instance config doesn't contain entry for {identifier}")
        try:
            return TicketHostModel(**data)
        except ValidationError as e:
            raise ConfigError(f"Invalid config for ticketing instance {identifier}: {e}")

    def write(self, branch_prefix: str, ticket_data: TicketHostModel):
        """Persist ticketing config for a branch prefix."""
        self._config_manager.update_config(
            "ticketing_instances",
            {branch_prefix: ticket_data.model_dump(exclude_none=True)},
        )
