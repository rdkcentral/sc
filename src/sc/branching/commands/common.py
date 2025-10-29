from ..branch import Branch, BranchType
from sc_manifest_parser import ProjectElementInterface

def get_alt_branch_name(branch: Branch, project: ProjectElementInterface) -> str | None:
    match branch:
        case BranchType.MASTER:
            return project.alternative_master
        case BranchType.DEVELOP:
            return project.alternative_develop
        case _:
            return None

def resolve_project_branch_name(branch: Branch, project: ProjectElementInterface) -> str:
    return get_alt_branch_name(branch, project) or branch.name