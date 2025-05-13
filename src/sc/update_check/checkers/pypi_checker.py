import click
import requests
from packaging import version

from sc.update_check.update_checker import UpdateChecker

class PyPiChecker(UpdateChecker):
    def get_latest_version(self, package_name):
        resp = requests.get(
            f"https://pypi.org/pypi/{package_name}/json", timeout=2)
        return version.Version(resp.json()['info']['version'])
    
    def print_install_message(self, package_name: str, version: version.Version):
        click.secho(
            f"To update {package_name} use command: "
            f"`pip install --upgrade {package_name}`",
            fg='green'
        )
