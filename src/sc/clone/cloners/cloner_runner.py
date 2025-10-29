import logging
from pathlib import Path
import sys
from typing import TYPE_CHECKING

from .cloner import Cloner
from .git_cloner import GitClonerConfig
from .git_flow_cloner import GitFlowCloner
from .repo_cloner import RepoCloner, RepoClonerConfig

if TYPE_CHECKING:
    from ..clone import CliOverrides
    from ..project_list.project_list import Project

logger = logging.getLogger(__name__)

class ClonerRunner:
    def clone(
            self, 
            directory: Path,
            project_config: "Project",
            cli_overrides: "CliOverrides"
        ) -> Cloner:
        cloner_type = project_config.type
        if cloner_type == "git":
            config = self._make_git_cloner_config(project_config, cli_overrides)
            cloner = GitFlowCloner(config)
        elif cloner_type == "repo":
            config = self._make_repo_cloner_config(project_config, cli_overrides)
            cloner = RepoCloner(config)
        else:
            raise ValueError(f"Invalid cloner type {cloner_type}")
        
        cloner.clone(directory)
    
    def _make_git_cloner_config(
            self, 
            project_config: "Project", 
            cli_overrides: "CliOverrides"
        ) -> GitClonerConfig:
        cloner_config = GitClonerConfig(
            uri = project_config.uri,
            branch = project_config.branch,
            no_tags = bool(cli_overrides.get('no_tags'))
        )

        if rev := cli_overrides.get("rev"):
            cloner_config.branch = rev 

        if cli_overrides.get("no_tags"):
            logger.info("Option [--no-tags]")
        
        return cloner_config
    
    def _make_repo_cloner_config(
            self,
            project_config: "Project",
            cli_overrides: "CliOverrides"
        ) -> RepoClonerConfig:
        if not project_config.manifest:
            logger.error(f"No manifest supplied for {project_config.name}!")
            sys.exit(1)

        cloner_config = RepoClonerConfig(
            uri = project_config.uri,
            branch = project_config.branch,
            no_tags = bool(cli_overrides.get('no_tags')),
            manifest = project_config.manifest,
            cache = project_config.effective_cache,
            repo_url = project_config.repo_url,
            repo_rev = project_config.repo_rev,
        )

        if rev := cli_overrides.get("rev"):
            cloner_config.branch = rev 

        if cli_overrides.get("no_tags"):
            logger.info("Option [--no-tags]: disabled cache")
            cloner_config.cache = False
        
        if cli_overrides.get("manifest"):
            logger.info(
                f"Option [-m] override manifest with [{cli_overrides.get('manifest')}]")
            cloner_config.manifest = cli_overrides.get("manifest")

        return cloner_config