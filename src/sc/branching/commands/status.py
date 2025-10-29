import subprocess
from pathlib import Path
from .command import Command
from repo_library import RepoLibrary



class Status(Command):
    def run_git_command(self):
        subprocess.run(
            ["git","status"],
            cwd = self.top_dir,
            encoding="utf-8",
            check=False,
        )
        
    def run_repo_command(self):
        RepoLibrary.status(self.top_dir)


            

