import subprocess

from .command import Command
from sc_manifest_parser import ScManifest

class Clean(Command):
    def _clean_repo(self,dir):
        subprocess.run(
            ["git","clean","-fdx","-e",f'".repo*"'],
            cwd = dir,
            encoding = "utf-8",
            check = False,
        )

    def run_git_command(self):
        self._clean_repo(self.top_dir)
    
    def run_repo_command(self):
        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        manifest_dir = self.top_dir / '.repo' / 'manifests'
        for project in manifest.projects:
            if project.lock_status is not None:
                continue
            self._clean_repo(self.top_dir) 
        self._clean_repo(manifest_dir)
