from importlib import metadata

from sc.update_check.update_checker import UpdateChecker
from sc.update_check.checkers.github_checker import GitHubChecker
from sc.update_check.checkers.pypi_checker import PyPiChecker

class CheckerFactory:
    def get_repo_url(self, package_name):
        try:
            meta = metadata.metadata(package_name)
            return meta.get('Home-page')
        except metadata.PackageNotFoundError:
            return None

    def select_checker(self, package_name) -> UpdateChecker:
        url = self.get_repo_url(package_name)

        if 'github.com' in url:
            return GitHubChecker(url)
        elif 'pypi' in url:
            return PyPiChecker()
        else:
            return None