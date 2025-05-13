from abc import ABC, abstractmethod
import logging
import pkg_resources

import click
from packaging import version
import requests

logger = logging.getLogger(__name__)

class UpdateChecker(ABC):
    @abstractmethod
    def get_latest_version(self, package_name) -> version.Version:
        pass

    @abstractmethod
    def print_install_message(self, package_name: str):
        pass

    def check_and_warn(self, package_name):
        try:
            current = version.parse(pkg_resources.get_distribution(package_name).version)
            latest = self.get_latest_version(package_name)
            if latest > current:
                click.secho(
                    f"Warning: {package_name} version {latest} is available "
                    f"(you have {current})"
                )
                self.print_install_message(package_name, latest)
                
        except Exception as e:
            logger.debug(f"Package name {package_name}'s version check failed: {e}")