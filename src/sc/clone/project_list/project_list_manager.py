import logging
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, model_validator, ValidationError

from .project_list import ProjectList
from .project_list_downloader import ProjectListDownloader

logger = logging.getLogger(__name__)

class ProjectListSource(BaseModel):
    """Information on how to load a ProjectList.
    
    In the context of this tool it will be stored in the sc config.
    """
    model_config = ConfigDict(extra='forbid')

    url: str
    path: str | None = None
    platform: str | None = None
    token: str | None = None

    @model_validator(mode='after')
    def check_platform_token_pair(self):
        if bool(self.platform) != bool(self.token):
            raise ValueError("Both 'platform' and 'token' must be set together.")
        return self

class ProjectListManager:
    def __init__(self, default_dir: Path):
        self.default_dir = default_dir

        self._project_list_downloader = ProjectListDownloader()
    
    @property
    def supported_platforms(self) -> list:
        """Return a list of supported platforms."""
        return list(self._project_list_downloader.supported_platforms.keys())

    def load_project_lists_from_config(self, config: dict) -> list[ProjectList]:
        """Download and load all project lists defined in the config."""
        sources = self._parse_project_list_sources(config)

        project_lists = []
        for name, source in sources:
            pl = self.load_project_list_from_source(name, source)
            if pl is not None:
                project_lists.append(pl)
        return project_lists
    
    def load_project_list_from_source(
            self, name: str, source: ProjectListSource) -> ProjectList | None:
        """Download and load a project list from a given source."""
        path = self._download_project_list(name, source)
        if path is None:
            return None
        return self.load_local_project_list(name, path)

    def load_local_project_list(self, name: str, path: Path) -> ProjectList | None:
        """Load a project list from a local yaml file."""
        try:
            return ProjectList(name, path)
        except IOError as e:
            logger.warning(f"Failed to load project list {name} from path {path}: {e}")
            return None

    def _parse_project_list_sources(self, config: dict) -> list[tuple[str, ProjectListSource]]:
        """Read and validate project list sources from config."""
        sources = []
        for name, raw_cfg in config.items():
            try:
                source = ProjectListSource(**raw_cfg)
                sources.append((name, source))
            except ValidationError as e:
                logger.warning(f"Invalid config for project list {name}: {e}")
        return sources
    
    def _download_project_list(
            self, name: str, source: ProjectListSource) -> Path | None:
        """Download the project list YAML from a remote URL."""
        if source.path is None:
            self.default_dir.mkdir(parents=True, exist_ok=True)
            path = self.default_dir / f"{name}.yaml"
        else:
            path = Path(source.path)

        try:
            logger.info(f"Downloading project list {name} to path {str(path)}")
            return self._project_list_downloader.download(
                source.url, path, source.platform, source.token)
        except (RuntimeError, IOError) as e:
            logger.warning(f"Failed to download project list {name}: {e}")
            return None
    