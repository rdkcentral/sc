import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys

from pydantic import BaseModel

from .cloner import Cloner, RefType
from repo_library import RepoLibrary
from sc.branching import SCBranching
from sc_manifest_parser import ScManifest

logger = logging.getLogger(__name__)

REPO_CACHE_DIR = Path.home() / ".caches"

class RepoClonerConfig(BaseModel):
    """
    Attributes:
        uri (str): The repository URL to clone.
        branch (str | None): The branch to clone. If None, the default branch is used.
        manifest (str | None): The name of the manifest file used for cloning.
            Defaults to "default.xml".
        no_tags (bool, optional): If True, disables fetching tags during cloning. 
            Defaults to False.
        repo_url (str | None): The repo url to be initialised and used for cloning.
        no_repo_verify (bool): Stops repo checking the validity of the version of repo
            used. Should be set to true if using a custom repo_url.
        repo_rev (str | None): The rev from the repo_url to be used. Defaults to None
            which uses the default revision.
        verify (bool): If True stops repo asking the user to run hooks. Defaults to False.
    """
    uri: str
    branch: str | None = None
    manifest: str | None = None
    no_tags: bool = False
    cache: bool = True
    repo_url: str | None = None
    repo_rev: str | None = None
    verify: bool = False

class RepoCloner(Cloner):
    """For cloning Git repositories using a manifest file and initializing GitFlow."""
    def __init__(
            self,
            config: RepoClonerConfig,
        ):
        self.config = config

    def clone(self, directory: Path):
        """
        Clones the Git repository using the provided manifest, synchronizes it, and initializes GitFlow.
        This method:
        - Creates a cache if requested.
        - Resolves the target directory for cloning.
        - Initializes and syncs the repository using `git_repo_utils`.
        - Parses the manifest to retrieve projects.
        - Initializes GitFlow for all unlocked projects.
        """
        reference = self._cache() if self.config.cache else None

        self._init_repo(directory=directory, reference=reference)
        RepoLibrary.sync(directory, self.config.no_tags)
        
        SCBranching.init(directory)

        manifest = ScManifest.from_repo_root(directory / '.repo')
        manifests_dir = Path(directory, '.repo', 'manifests')
        for hook in manifest.post_sync_scripts:
            self._run_post_sync_script(manifests_dir / hook.path)
    
    def _cache(self) -> Path:
        """Creates a cache of a project.

        Returns:
            Path: The directory of the mirrored cache.
        """
        REPO_CACHE_DIR.mkdir(exist_ok=True)
        manifest_hostname = self._get_manifest_hostname(self.config.uri)
        host_cache_dir = Path(REPO_CACHE_DIR / manifest_hostname)
        host_cache_dir.mkdir(exist_ok=True)

        # .repo file must be removed to run repo init --mirror
        if Path(host_cache_dir / '.repo').exists():
            shutil.rmtree(host_cache_dir / '.repo')

        self._init_repo(host_cache_dir, mirror=True)
        RepoLibrary.sync(directory=host_cache_dir)
        return host_cache_dir

    def _init_repo(self, directory: Path, mirror: bool = False, reference: Path | None = None):
        # If mirror is true we're creating a cache
        groups = "default,-notcached" if mirror else None
        
        ref_type = self._is_branch_tag_or_sha(self.config.uri, self.config.branch)
        
        if ref_type == RefType.TAG:
            ref = f"refs/tags/{self.config.branch}"
        else:
            ref = self.config.branch

        RepoLibrary.init(
            self.config.uri, 
            branch = ref,
            directory = directory,
            manifest = self.config.manifest,
            mirror = mirror,
            reference = reference,
            groups = groups,
            repo_url = self.config.repo_url,
            no_repo_verify = True,
            repo_rev = self.config.repo_rev,
            verify=self.config.verify
        )

    def _get_manifest_hostname(self, url: str) -> str:
        """Extracts the hostname from a given URL. 

        Example:
            _get_manifest_hostname("ssh://user@github.com:repo/path") -> "github.com"
        """
        url = url.split("://", 1)[-1]        
        url = url.split("@", 1)[-1]        
        url = url.split(":", 1)[0]
        url = url.split("/", 1)[0]
        return url
    
    def _run_post_sync_script(self, path: Path):
        if not path:
            logger.warning(
                "post-sync element has no path attribute and is being skipped!")
            return

        if not os.access(path, os.X_OK):
            logger.warning(
                f"post-sync path {path} is not executable and is being skipped!")
            return

        subprocess.run(str(path), shell=True)
