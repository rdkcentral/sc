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

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
import re
from urllib import parse

from git import Repo

from git_flow_library import GitFlowLibrary
from sc_manifest_parser import ScManifest
from .exceptions import RemoteUrlNotFound, TicketIdentifierNotFound
from .review_config import ReviewConfig, TicketHostCfg
from .ticketing_instances.ticket_instance_factory import TicketingInstanceFactory
from .ticketing_instances.ticketing_instance import TicketingInstance
from .git_instances.git_factory import GitFactory
from .git_instances.git_instance import GitInstance

logger = logging.getLogger(__name__)

@dataclass
class CommentData:
    branch: str
    directory: str | Path
    remote_url: str
    review_status: str
    review_url: str | None
    create_pr_url: str
    commit_sha: str
    commit_author: str
    commit_date: datetime
    commit_message: str


class Review:
    def __init__(self, top_dir: Path | str):
        self.top_dir = Path(top_dir)

        self._config = ReviewConfig()

    def run_git_command(self):
        branch_name = Repo(self.top_dir).active_branch.name
        try:
            identifier, ticket_num = self._match_branch(branch_name)
        except TicketIdentifierNotFound as e:
            logger.warning(e)
            identifier, ticket_num = self._prompt_ticket_selection()

        ticketing_cfg = self._config.get_ticket_host_data(identifier)
        ticketing_instance = self._create_ticketing_instance(identifier)

        ticket_id = f"{ticketing_cfg.project_prefix or ''}{ticket_num}"
        ticket = ticketing_instance.read_ticket(ticket_id)

        git_instance = self._create_git_instance(Repo(self.top_dir).remote().url)
        comment_data = self._create_comment_data(Repo(self.top_dir), git_instance)

        logger.info(f"Ticket URL: [{ticket.url if ticket else 'None'}]")
        logger.info("Ticket info: ")
        print(self._generate_terminal_comment(comment_data))

        if self._prompt_yn("Update ticket?"):
            ticket_comment = self._generate_ticket_comment(comment_data)
            ticketing_instance.add_comment_to_ticket(ticket_id, ticket_comment)

    def run_repo_command(self):
        manifest_repo = Repo(self.top_dir / '.repo' / 'manifests')

        try:
            identifier, ticket_num = self._match_branch(manifest_repo.active_branch.name)
        except TicketIdentifierNotFound as e:
            logger.warning(e)
            identifier, ticket_num = self._prompt_ticket_selection()

        ticketing_cfg = self._config.get_ticket_host_data(identifier)
        ticketing_instance = self._create_ticketing_instance(identifier)

        ticket_id = f"{ticketing_cfg.project_prefix or ''}{ticket_num}"
        ticket = ticketing_instance.read_ticket(ticket_id)

        logger.info(f"Ticket URL: [{ticket.url if ticket else ''}]")
        logger.info("Ticket info: ")

        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        comments = []
        for project in manifest.projects:
            if project.lock_status:
                continue

            proj_repo = Repo(self.top_dir / project.path)
            # Don't generate for projects that haven't got an upstream
            if not proj_repo.active_branch.tracking_branch():
                continue

            proj_git = self._create_git_instance(proj_repo.remotes[project.remote].url)
            comment_data = self._create_comment_data(
                proj_repo, proj_git)
            comments.append(comment_data)

        manifest_git = self._create_git_instance(manifest_repo.remote().url)
        comment_data = self._create_comment_data(
            manifest_repo, manifest_git)
        comments.append(comment_data)

        print(self._generate_combined_terminal_comment(comments))

        if self._prompt_yn("Update ticket?"):
            ticket_comment = self._generate_combined_ticket_comment(comments)
            ticketing_instance.add_comment_to_ticket(ticket_id, ticket_comment)

    def _match_branch(self, branch_name: str) -> tuple[str, str]:
        """Match the branch to an identifier in the config.

        Args:
            branch_name (str): The current branch name.

        Raises:
            TicketIdentifierNotFound: Raised when the branch doesn't match any
                identifiers in the ticket host config.

        Returns:
            tuple[str, str]: (matched_identifier, ticket_number)
        """
        host_identifiers = self._config.get_ticket_host_identifiers()
        for identifier in host_identifiers:
            # Matches the identifier, followed by - or _, followed by a number
            if m := re.search(fr'{identifier}[-_]?(\d+)', branch_name):
                ticket_num = m.group(1)
                return identifier, ticket_num
        raise TicketIdentifierNotFound(
            f"Branch {branch_name} doesn't match any ticketing instances! "
            f"Found instances {', '.join(host_identifiers)}")

    def _create_git_instance(self, remote_url: str) -> GitInstance:
        git_url_patterns = self._config.get_git_patterns()
        try:
            remote_pattern = self._match_remote_url(
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

    def _match_remote_url(
            self,
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

    def _get_repo_slug(self, remote_url: str) -> str:
        """Return the repository slug (e.g. "org/repo") from a remote url."""
        if remote_url.startswith("git@"):
            slug = remote_url.split(":", 1)[1]
        else:
            slug = parse.urlparse(remote_url).path.lstrip("/")

        if slug.endswith(".git"):
            slug = slug[:-4]

        return slug

    def _get_target_branch(self, directory: Path, source_branch: str) -> str:
        if GitFlowLibrary.is_gitflow_enabled(directory):
            base = GitFlowLibrary.get_branch_base(source_branch, directory)
            return base if base else GitFlowLibrary.get_develop_branch(directory)
        else:
            return "develop"

    def _prompt_yn(self, msg: str) -> bool:
        return input(f"{msg} (y/n): ").strip().lower() == 'y'

    def _create_comment_data(self, repo: Repo, git_instance: GitInstance) -> CommentData:
        branch_name = repo.active_branch.name
        repo_slug = self._get_repo_slug(repo.remotes[0].url)
        cr = git_instance.get_code_review(repo_slug, branch_name)

        target_branch = self._get_target_branch(repo.working_dir, branch_name)
        create_pr_url = git_instance.get_create_cr_url(
            repo_slug, branch_name, target_branch)

        commit = repo.head.commit

        review_status = str(cr.status) if cr else "Not Created"
        review_url = cr.url if cr else None

        return CommentData(
            branch=branch_name,
            directory=repo.working_dir,
            remote_url=repo.remotes[0].url,
            review_status=review_status,
            review_url=review_url,
            create_pr_url=create_pr_url,
            commit_sha=commit.hexsha[:10],
            commit_author=f"{commit.author.name} <{commit.author.email}>",
            commit_date=commit.committed_datetime,
            commit_message=commit.message.strip()
        )

    def _create_ticketing_instance(self, cfg: TicketHostCfg) -> TicketingInstance:
        inst = TicketingInstanceFactory.create(
            provider=cfg.provider,
            url=cfg.url,
            token=cfg.api_key,
            auth_type=cfg.auth_type,
            username=cfg.username,
            cert=cfg.cert
        )
        return inst

    def _prompt_ticket_selection(self) -> tuple[TicketingInstance, str]:
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
        return "\n\n".join(self._generate_terminal_comment(c) for c in comments)

    def _generate_combined_ticket_comment(self, comments: list[CommentData]) -> str:
        return "\n\n".join(self._generate_ticket_comment(c) for c in comments)

    def _generate_terminal_comment(self, data: CommentData) -> str:
        """Generate the information for one repo to be displayed in the terminal.

        Args:
            data (CommentData): The data collated from one repo.

        Returns:
            str: Information from one repo to be displayed in the terminal.
        """
        def c(code, text):
            return f"\033[{code}m{text}\033[0m"

        header = [
            f"Branch: [{data.branch}]",
            f"Directory: [{data.directory}]",
            f"Git: [{data.remote_url}]",
        ]

        if data.review_url:
            review_status = f"Review Status: [{c('32', data.review_status)}]"
            review_link = f"Review URL: [{c('32', data.review_url)}]"
        else:
            review_status = f"Review Status: [{c('31', data.review_status)}]"
            review_link = f"Create Review URL: [{c('33', data.create_pr_url)}]"

        review = [review_status, review_link]

        commit = (
            f"Last Commit: [{data.commit_sha}]",
            f"Author: [{data.commit_author}]",
            f"Date: [{data.commit_date}]",
            "",
            f"{data.commit_message}"
        )

        return "\n".join([*header, "", *review, "", *commit])

    def _generate_ticket_comment(self, data: CommentData) -> str:
        """Generate the information for one repo formatted for a ticket comment.

        Args:
            data (CommentData): The data collated for one repo.

        Returns:
            str: A formatted ticket comment.
        """
        header = [
            f"Branch: [{data.branch}]",
            f"Directory: [{data.directory}]",
            f"Git: [{data.remote_url}]",
        ]

        if data.review_url:
            review_status = f"Review Status: [{data.review_status}]"
            review_link = f"Review URL: [{data.review_url}]"
        else:
            review_status = f"Review Status: [{data.review_status}]"
            review_link = f"Create Review URL: [{data.create_pr_url}]"

        review = [review_status, review_link]

        commit = (
            "<pre>",
            f"Last Commit: [{data.commit_sha}]",
            f"Author: [{data.commit_author}]",
            f"Date: [{data.commit_date}]",
            "",
            f"{data.commit_message}",
            "</pre>"
        )

        return "\n".join([*header, "", *review, "", *commit])
