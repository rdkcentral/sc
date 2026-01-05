# Copyright 2025 RDK Management
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import getpass
import logging
from pathlib import Path
import sys

from git_flow_library import GitFlowLibrary
from repo_library import RepoLibrary
from .exceptions import ReviewException
from .review import Review
from .review_config import ReviewConfig, TicketHostCfg, GitInstanceCfg
from .ticketing_instances.ticket_instance_factory import TicketingInstanceFactory
from .git_instances.git_factory import GitFactory

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

def add_git_instance():
    logger.info("Enter Git provider from the list below: ")
    logger.info("github")
    logger.info("gitlab")

    provider = input("> ")
    print("")

    if provider == "github":
        url = "https://api.github.com"
        logger.info("Enter a pattern to identify Git from remote url: ")
        logger.info(
            "E.G. github.com for all github instances or "
            "github.com/org for a particular organisation")
        pattern = input("> ")
        print("")
    elif provider == "gitlab":
        logger.info(
            "Enter the URL for the gitlab instance (e.g. https://gitlab.com "
            "or https://your-instance.com): ")
        url = input("> ")
        print("")
        pattern = url.replace("https://", "").replace("http://", "")
    else:
        logger.error("Provider matches none in the list!")


    logger.info("Enter your api token: ")
    api_key = input("> ")
    print("")

    instance = GitFactory.create(provider, api_key, url)

    try:
        instance.validate_connection()
    except ConnectionError as e:
        logger.error(f"Failed to connect! {e}")
        sys.exit(1)

    logger.info("Connection validated!")

    git_cfg = GitInstanceCfg(url=url, token=api_key, provider=provider)
    ReviewConfig().write_git_data(pattern, git_cfg)

    logger.info("Git Provider Added!")

def add_ticketing_instance():
    logger.info("Enter the ticketing provider from the list below: ")
    logger.info("jira")
    logger.info("redmine")
    provider = input("> ")
    print("")

    if provider not in ("jira", "redmine"):
        logger.error(f"Provider {provider} not supported!")
        sys.exit(1)

    logger.info("Enter the branch prefix (e.g ABC for feature/ABC-123_ticket): ")
    branch_prefix = input("> ")
    print("")

    if provider == "jira":
        project_prefix = f"{branch_prefix}-"

        logger.info("Auth type:")
        logger.info("token")
        logger.info("basic")
        auth_type = input("> ")
        print("")

        if auth_type not in ("token", "basic"):
            logger.error(f"Auth type {auth_type} not supported!")
            sys.exit(1)

        if auth_type == "basic":
            logger.info("Username:")
            username = input("> ")
            print("")

    else:
        project_prefix = None
        username = None
        auth_type = "token"

    logger.info("Enter the base URL: ")
    base_url = input("> ")
    print("")

    logger.info("API token or password: ")
    api_token = getpass.getpass("> ")
    print("")

    instance = TicketingInstanceFactory.create(
        provider=provider,
        url=base_url,
        token=api_token,
        auth_type=auth_type,
        username=username
    )
    try:
        instance.validate_connection()
    except ConnectionError as e:
        logger.error(f"Failed to connect! {e}")
        sys.exit(1)

    logger.info("Connection successful!")

    ticket_cfg = TicketHostCfg(
        url=base_url,
        provider=provider,
        api_key=api_token,
        username=username,
        auth_type=auth_type,
        project_prefix=project_prefix
    )

    ReviewConfig().write_ticketing_data(branch_prefix, ticket_cfg)

    logger.info("Added ticketing instance!")
