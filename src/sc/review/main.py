import getpass
import logging
from pathlib import Path
import sys

from git_flow_library import GitFlowLibrary
from repo_library import RepoLibrary
from .exceptions import ReviewException
from .review import Review
from .review_config import ReviewConfig, TicketHostCfg, VcsCfg
from .ticketing_instances.ticket_instance_factory import TicketingInstanceFactory
from .vcs_instances.vcs_factory import VcsFactory

logger = logging.getLogger(__name__)

def review():
    try:
        if root := RepoLibrary.get_repo_root_dir(Path.cwd()):
            Review(root.parent).run_repo_command()
        elif root := GitFlowLibrary.get_git_root(Path.cwd()):
            Review(root.parent).run_git_command()
        else:
            logger.error("Not in a repo project or git repository!")
            sys.exit(1)
    except ReviewException as e:
        logger.error(e)
        sys.exit(1)

def add_vcs_instance():
    logger.info("Enter VCS provider from the list below: ")
    logger.info("github")
    logger.info("gitlab")

    provider = input("> ")
    print("")
    if provider == "github":
        url = "http://api.github.com"
    elif provider == "gitlab":
        logger.info("Enter the URL for the gitlab instance (e.g. https://gitlab.com): ")
        url = input("> ")
        print("")
    else:
        logger.error("Provider matches none in the list!")
    
    logger.info("Enter a pattern for to identify VCS from remote url: ")
    logger.info("E.G. github.com for all github instances or github.com/org for a particular organisation")
    pattern = input("> ")
    print("")
    
    logger.info("Enter your api token: ")
    api_key = input("> ")
    print("")

    instance = VcsFactory.create(provider, api_key, url)

    if instance.validate_connection():
        logger.info("Connection validated!")
    else:
        logger.error("Failed to validate connection!")
        sys.exit(1)
    
    vcs_cfg = VcsCfg(url=url, token=api_key, provider=provider)
    ReviewConfig.add_vcs_instance(pattern, vcs_cfg)

    logger.info("VCS Provider Added!")

def add_ticketing_instance():
    logger.info("Enter the branch prefix (e.g ABC for feature/ABC-123_ticket): ")
    branch_prefix = input("> ")
    print("")

    logger.info("Enter the ticketing provider from the list below: ")
    logger.info("jira")
    logger.info("redmine")
    provider = input("> ")
    print("")

    if provider not in ("jira", "redmine"):
        logger.error(f"Provider {provider} not supported!")
        sys.exit(1)
    
    if provider == "jira":
        project_prefix = f"{branch_prefix}-"
    else:
        project_prefix = None

    logger.info("Enter the base URL: ")
    base_url = input("> ")
    print("")

    logger.info("API token or password: ")
    api_token = getpass.getpass("> ")
    print("")

    instance = TicketingInstanceFactory.create(
        provider=provider, 
        url=base_url,
        token=api_token
    )
    if instance.validate_connection():
        logger.info("Connection validated!")
    else:
        logger.info("Failed to validate connection!")

    ticket_cfg = TicketHostCfg(
        url=base_url, 
        provider=provider, 
        api_key=api_token, 
        project_prefix=project_prefix
    )
    
    ReviewConfig.write_ticketing_data(branch_prefix, ticket_cfg)
