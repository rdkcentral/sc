import urllib
import urllib.parse

import click
from packaging import version
import requests

from sc.update_check.update_checker import UpdateChecker

class GitHubChecker(UpdateChecker):
    def __init__(self, url: str):
        self.repo = self._extract_github_repo(url)
    
    def get_latest_version(self, package_name: str) -> version.Version:
        resp = requests.get(
            f'https://api.github.com/repos/{self.repo}/releases/latest', timeout=2)
        return version.Version(resp.json()['tag_name'])
    
    def print_install_message(self, package_name: str, version: version.Version):
        click.secho(
            f"To update {package_name} use command: "
            f"`pip install --force-reinstall "
            f"git+https://github.com/{self.repo}.git@{str(version)}`",
            fg="green"
        )
    
    def _extract_github_repo(url: str) -> str:
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.netloc != "github.com":
            return None
        
        parts = parsed_url.path.strip("/").split("/")
        if len(parts) < 2:
            return None
        
        owner, repo = parts[0], parts[1].removesuffix(".git")
        return f"{owner}/{repo}"
        
