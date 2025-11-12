
from sc.config_manager import ConfigManager

from pydantic import BaseModel, ConfigDict, ValidationError

class TicketHostCfg(BaseModel):
    model_config = ConfigDict(extra='forbid')

    url: str
    class_name: str
    username: str | None = None
    api_key: str
    project_prefix: str | None = None
    description: str | None = None

class VcsCfg(BaseModel):
    model_config = ConfigDict(extra='forbid')

    url: str | None = None
    token: str
    provider: str

class ReviewConfig:
    def __init__(self):
        self._ticket_config = ConfigManager('ticketing_instances')
        self._vcs_config = ConfigManager('vcs_instances')
    
    def get_ticketing_config(self) -> dict[str, TicketHostCfg]:
        return {k: TicketHostCfg(**v) for k,v in self._ticket_config.get_config().items()}
    
    def get_ticket_host_ids(self) -> set[str]:
        return self._ticket_config.get_config().keys()
    
    def get_ticket_host_data(self, identifier: str) -> TicketHostCfg:
        data = self._ticket_config.get_config().get(identifier)
        if not data:
            raise KeyError(f"VCS config doesn't contain entry for {identifier}")
        try:
            return TicketHostCfg(**data)
        except ValidationError as e:
            raise ValueError(f"Invalid config for {identifier}: {e}")
    
    def write_ticketing_data(self, branch_prefix: str, ticket_data: TicketHostCfg):
        self._ticket_config.update_config({branch_prefix: {ticket_data.model_dump()}})
    
    def get_vcs_patterns(self) -> set[str]:
        return self._vcs_config.get_config().keys()
        
    def get_vcs_data(self, url_pattern: str) -> VcsCfg:
        data = self._vcs_config.get_config().get(url_pattern)
        if not data:
            raise KeyError(f"VCS config doesn't contain entry for {url_pattern}")
        try:
            return VcsCfg(**data)
        except ValidationError as e:
            raise ValueError(f"Invalid config for {url_pattern}: {e}")
    
    def write_vcs_data(self, pattern: str, vcs_config: VcsCfg):
        self._vcs_config.update_config({pattern: vcs_config.model_dump()})
    