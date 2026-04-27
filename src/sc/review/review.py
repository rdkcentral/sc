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

from collections.abc import Callable, Iterable
import logging
from pathlib import Path
import re
from urllib import parse

from git import Repo

from .exceptions import RemoteUrlNotFound, TicketIdentifierNotFound
from .git_instances import GitFactory, GitInstance
from .git_flow_branch_strategy import GitFlowBranchStrategy
from .models import CodeReview, CommentData, RepoInfo
from .repo_source import RepoSource
from .review_config import ReviewConfig, TicketHostCfg
from sc_manifest_parser import ScManifest
from .ticketing_instances import TicketingInstance, TicketingInstanceFactory
from .ticket_service import TicketService

logger = logging.getLogger(__name__)

class Review:
    def __init__(
            self,
            repo_source: RepoSource,
            ticket_service: TicketService | None = None,
            branch_strategy: GitFlowBranchStrategy | None = None,
        ):
        self.repo_source = repo_source
        self._ticket_service = ticket_service if ticket_service else TicketService()
        self._branch_strategy = branch_strategy if branch_strategy else GitFlowBranchStrategy()
        self._config = ReviewConfig()

    def run(self):
        try:
            identifier, ticket_num = self._ticket_service.match_branch(
                self.repo_source.active_branch)
        except TicketIdentifierNotFound as e:
            logger.warning(e)
            identifier, ticket_num = self._prompt_ticket_selection()

        ticket_instance, ticket = self._ticket_service.resolve(identifier, ticket_num)

        comments = []
        for repo_info in self.repo_source.get_repos():
            git_instance = self._create_git_instance(repo_info.remote_url)
            comments.append(self._build_comment_data(repo_info, git_instance))

        logger.info(f"Ticket URL: [{ticket.url if ticket else 'None'}]")
        logger.info("Ticket info: \n")
        print(self._generate_combined_terminal_comment(comments))
        print()

        if self._prompt_yn("Update ticket?"):
            ticket_comment = self._generate_combined_ticket_comment(comments)
            self._ticket_service.update(ticket_instance, ticket.id, ticket_comment)

    def _create_git_instance(self, remote_url: str) -> GitInstance:
        git_url_patterns = self._config.get_git_patterns()
        try:
            remote_pattern = match_remote_url(
                remote_url, git_url_patterns)
        except RemoteUrlNotFound as e:
            raise RemoteUrlNotFound(
                str(e) + f"\nRemotes patterns found: {', '.join(git_url_patterns)}"
            )
        git_data = self._config.get_git_data(remote_pattern)
        return GitFactory.create(
            git_data.provider,
            token=git_data.token,
            base_url=git_data.url
        )

    def _prompt_yn(self, msg: str) -> bool:
        return input(f"{msg} (y/n): ").strip().lower() == 'y'

    def _build_comment_data(
        self,
        repo_info: RepoInfo,
        git_instance: GitInstance,
    ) -> CommentData:
        target_branch = self._branch_strategy.get_target_branch(
            repo_info.directory, repo_info.branch)
        cr, create_pr_url = get_git_review_data(
            repo_info, git_instance, target_branch
        )
        return self._create_comment_data(repo_info, create_pr_url, cr)

    def _create_comment_data(
            self,
            repo_info: RepoInfo,
            create_pr_url: str,
            cr: CodeReview | None) -> CommentData:
        review_status = str(cr.status) if cr else "Not Created"
        review_url = cr.url if cr else None

        return CommentData(
            branch=repo_info.branch,
            directory=repo_info.directory,
            remote_url=repo_info.remote_url,
            review_status=review_status,
            review_url=review_url,
            create_pr_url=create_pr_url,
            commit_sha=repo_info.commit_sha,
            commit_author=repo_info.commit_author,
            commit_date=repo_info.commit_date,
            commit_message=repo_info.commit_message
        )

    def _create_ticketing_instance(self, cfg: TicketHostCfg) -> TicketingInstance:
        """Create a ticketing instance.

        Args:
            cfg (TicketHostCfg): Config describing a ticketing instance.

        Raises:
            ConnectionError: Failed to connect to ticketing instance.

        Returns:
            TicketingInstance: A ticketing instance class.
        """
        inst = TicketingInstanceFactory.create(
            provider=cfg.provider,
            url=cfg.url,
            token=cfg.api_key,
            auth_type=cfg.auth_type,
            username=cfg.username,
            cert=cfg.cert
        )
        return inst

    def _prompt_ticket_selection(self) -> tuple[str, str]:
        """Prompt the user to select a ticketing instance and enter a ticket number.

        Raises:
            TicketIdentifierNotFound: If the instance identifier doesn't match any
                in the config.

        Returns:
            tuple[str, str]: The selected ticketing instance identifier and ticket
                number.
        """
        ticket_conf = self._config.get_ticketing_config()
        logger.info("Please enter the prefix of the ticket instance:")
        logger.info("PREFIX --- INSTANCE URL --- DESCRIPTION")
        for id, conf in ticket_conf.items():
            logger.info(f"{id} --- {conf.url} --- {conf.description or ''}")

        input_id = input("> ")
        while input_id not in ticket_conf.keys():
            logger.info(f"Prefix {input_id} not found in instances.")
            input_id = input("> ")

        logger.info("Please enter your ticket number:")
        input_num = input("> ")

        return input_id, input_num

    def _generate_combined_terminal_comment(self, comments: list[CommentData]) -> str:
        return "\n\n".join(c.to_terminal() for c in comments)

    def _generate_combined_ticket_comment(self, comments: list[CommentData]) -> str:
        return "\n\n".join(c.to_ticket() for c in comments)

def get_repo_slug(remote_url: str) -> str:
    """Return the repository slug (e.g. "org/repo") from a remote url."""
    if remote_url.startswith("git@"):
        slug = remote_url.split(":", 1)[1]
    else:
        slug = parse.urlparse(remote_url).path.lstrip("/")

    slug = slug.strip("/")

    if slug.endswith(".git"):
        slug = slug[:-4]

    return slug

def match_remote_url(
        remote_url: str,
        git_patterns: Iterable[str]
    ) -> str:
    """Match the remote url to a pattern in the git instance config.

    Args:
        remote_url (str): The remote url of the git repository.
        git_patterns (Iterable[str]): An iterable of patterns to check against.

    Raises:
        RemoteUrlNotFound: Raised when the remote url matches no patterns.

    Returns:
        str: The matched pattern.
    """
    for pattern in git_patterns:
        if pattern in remote_url:
            return pattern
    raise RemoteUrlNotFound(f"{remote_url} doesn't match any patterns!")

def get_git_review_data(
        repo_info: RepoInfo, git_instance: GitInstance, target_branch: str):
    repo_slug = get_repo_slug(repo_info.remote_url)

    cr = git_instance.get_code_review(repo_slug, repo_info.branch)
    create_pr_url = git_instance.get_create_cr_url(
        repo_slug, repo_info.branch, target_branch
    )

    return cr, create_pr_url
