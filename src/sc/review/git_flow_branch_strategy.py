from pathlib import Path

from git_flow_library import GitFlowLibrary

class GitFlowBranchStrategy:
    def get_target_branch(self, directory: Path, source_branch: str) -> str:
        if GitFlowLibrary.is_gitflow_enabled(directory):
            base = GitFlowLibrary.get_branch_base(source_branch, directory)
            return base if base else GitFlowLibrary.get_develop_branch(directory)
        else:
            return "develop"
