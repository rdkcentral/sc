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
from .exceptions import RemoteUrlNotFound, TicketIdentifierNotFound, TicketNotFound
from .review_config import ReviewConfig
from .ticketing_instances.ticket_instance_factory import TicketingInstanceFactory
from .ticketing_instances.ticketing_instance import TicketingInstance
from .vcs_instances.vcs_factory import VcsFactory
from .vcs_instances.vcs_instance import VcsInstance

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

    def generate_comment(self, formatted: bool = False) -> str:
        header = [
            f"Branch: [{self.branch}]",
            f"Directory: [{self.directory}]",
            f"Git: [{self.remote_url}]",
        ]
        
        review = [
            f"Review Status: [{self.review_status}]",
            f"Review URL: [{self.review_url}]" if self.review_url else
            f"Create Review URL: [{self.create_pr_url}]"
        ]

        commit = (
            f"Last Commit: [{self.commit_sha}]",
            f"Author: [{self.commit_author}]",
            f"Date: [{self.commit_date}]",
            "",
            f"{self.commit_message}"
        )

        if formatted:
            commit = ["<pre>", *commit, "</pre>"]
        
        return "\n".join(
            [
                *header,
                "",
                *review,
                "",
                *commit
            ]
        )

class Review:
    def __init__(self, top_dir: str):
        self.top_dir = top_dir

        self._config = ReviewConfig()

    def run_git_command(self):
        ticket_host_ids = self._config.get_ticket_host_ids()
        branch_name = Repo(self.top_dir).active_branch.name
        try:
            identifier, ticket_num = self._match_branch(
                branch_name,
                ticket_host_ids
            )
        except TicketIdentifierNotFound as e:
            logger.warning(e)
            identifier, ticket_num = None, None

        if identifier and ticket_num:
            ticket_host_data = self._config.get_ticket_host_data(identifier)
            ticketing_instance: TicketingInstance = TicketingInstanceFactory.create(
                ticket_host_data.class_name,
                ticket_host_data.url, 
                ticket_host_data.api_key, 
                ticket_host_data.username
            )
            
            ticket_id = f"{ticket_host_data.project_prefix or ''}{ticket_num}"
            ticket = ticketing_instance.read_ticket(ticket_id)
        else:
            ticketing_instance = None
            ticket = None
        
        vcs_instance = self._create_vcs_instance(Repo(self.top_dir).remote().url)
        comment_data = self._create_comment_data(Repo(self.top_dir), vcs_instance)

        logger.info(f"Ticket URL: [{ticket.url if ticket else 'None'}]")
        logger.info("Ticket info: ")
        print(comment_data.generate_comment())
        
        if self._prompt_yn("Update ticket?"):
            if ticketing_instance and ticket_id:
                ticketing_instance.add_comment_to_ticket(
                    ticket_id, comment_data.generate_comment(formatted=True))
            else:
                ticketing_instance, ticket_id = self._prompt_ticket_selection()
                ticketing_instance.add_comment_to_ticket(
                    ticket_id, comment_data.generate_comment(formatted=True))
        
    def run_repo_command(self):
        manifest_repo = Repo(self.top_dir / '.repo' / 'manifests')

        ticket_host_ids = self._config.get_ticket_host_ids()

        try:
            identifier, ticket_num = self._match_branch(
                manifest_repo.active_branch.name,
                ticket_host_ids
            )
        except TicketIdentifierNotFound as e:
            logger.warning(e)
            identifier, ticket_num = None, None

        if identifier and ticket_num: 
            ticket_host_data = self._config.get_ticket_host_data(identifier)
            ticketing_instance = TicketingInstanceFactory.create(
                ticket_host_data.class_name,
                ticket_host_data.url,
                ticket_host_data.api_key,
                ticket_host_data.username
            )
            
            ticket_id = f"{ticket_host_data.project_prefix or ''}{ticket_num}"
            ticket = ticketing_instance.read_ticket(ticket_id)
        else:
            ticketing_instance, ticket_id = None, None

        logger.info(f"Ticket URL: [{ticket.url if ticket else ''}]")
        logger.info("Ticket info: ")

        manifest = ScManifest.from_repo_root(self.top_dir / '.repo')
        comments = []
        for project in manifest.projects:
            proj_repo = Repo(self.top_dir / project.path)
            proj_vcs = self._create_vcs_instance(proj_repo.remotes[proj_repo.remote].url)
            comment_data = self._create_comment_data(
                proj_repo, proj_vcs)
            comments.append(comment_data)

        manifest_vcs = self._create_vcs_instance(manifest_repo.remote().url)
        comment_data = self._create_comment_data(
            manifest_repo, manifest_vcs)
        comments.append(comment_data)       

        multi_repo_comment = self._generate_multi_comment(comments)
        print(multi_repo_comment)

        if self._prompt_yn("Update ticket?"):
            if ticketing_instance and ticket_id:
                ticketing_instance.add_comment_to_ticket(
                    ticket_id, multi_repo_comment)
            else:
                ticketing_instance, ticket_id = self._prompt_ticket_selection()
                ticketing_instance.add_comment_to_ticket(
                    ticket_id, multi_repo_comment)
    
    def _match_branch(
        self, 
        branch_name: str, 
        host_identifiers: Iterable[str]
    ) -> tuple[str, str]:
        """Match the branch to an identifier in the config.

        Args:
            branch_name (str): The current branch name.
            host_identifiers (Iterable[str]): An iterable of ticket host identifiers.

        Raises:
            TicketIdentifierNotFound: Raised when the branch doesn't match any
                identifiers in the ticket host config.

        Returns:
            tuple[str, str]: (matched_identifier, ticket_number)
        """        
        for identifier in host_identifiers:
            # Matches the identifier, followed by - or _, followed by a number
            if m := re.search(fr'{identifier}[-_]?(\d+)', branch_name):
                ticket_num = m.group(1)
                return identifier, ticket_num
        raise TicketIdentifierNotFound(
            f"Branch {branch_name} doesn't match any ticketing instances! "
            f"Found instances {', '.join(host_identifiers)}")
    
    def _create_vcs_instance(self, remote_url: str) -> VcsInstance:
        vcs_url_patterns = self._config.get_vcs_patterns()
        try:
            remote_pattern = self._match_remote_url(
                remote_url, vcs_url_patterns)
        except RemoteUrlNotFound as e:
            raise RemoteUrlNotFound(
                e + f"\nRemotes patterns found: {', '.join(vcs_url_patterns)}"
            )
        vcs_data = self._config.get_vcs_data(remote_pattern)
        return VcsFactory.create(
            vcs_data.provider,
            token=vcs_data.token,
            base_url=vcs_data.url
        )
    
    def _match_remote_url(
            self,
            remote_url: str,
            vcs_patterns: Iterable[str]
        ) -> str:
        """Match the remote url to a pattern in the vcs config.

        Args:
            remote_url (str): The remote url of the git repository.
            vcs_patterns (Iterable[str]): An iterable of patterns to check against.

        Raises:
            RemoteUrlNotFound: Raised when the remote url matches no patterns.

        Returns:
            str: The matched pattern.
        """        
        for pattern in vcs_patterns:
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
        base = GitFlowLibrary.get_branch_base(source_branch, directory)
        return base if base else GitFlowLibrary.get_develop_branch(directory)
    
    def _prompt_yn(self, msg: str) -> bool:
        return input(f"{msg} (y/n): ").strip().lower() == 'y'
    
    def _create_comment_data(self, repo: Repo, vcs_instance: VcsInstance) -> CommentData:
        branch_name = repo.active_branch.name
        repo_slug = self._get_repo_slug(repo.remote().url)
        pr = vcs_instance.get_pull_request(repo_slug, branch_name)

        target_branch = self._get_target_branch(self.top_dir, branch_name)
        create_pr_url = vcs_instance.get_create_pr_url(
            repo_slug, branch_name, target_branch)
        
        commit = repo.head.commit

        review_status = pr.status if pr else "Not Created"
        review_url = pr.url if pr else None

        return CommentData(
            branch=branch_name,
            directory=repo.working_dir,
            remote_url=repo.remote().url,
            review_status=review_status,
            review_url=review_url,
            create_pr_url=create_pr_url,
            commit_sha=commit.hexsha[:10],
            commit_author=f"{commit.author.name} <{commit.author.email}>",
            commit_date=commit.committed_datetime,
            commit_message=commit.message.strip()
        )
    
    def _generate_combined_comment(
            comments: list[CommentData], formatted: bool = False) -> str:
        parts = []
        for c in comments:
            parts.append(f"{c.generate_comment(formatted=formatted)}\n")
        return "\n".join(parts)

    def _prompt_ticket_selection(self) -> tuple[TicketingInstance, str]:
        """Prompt the user to select a ticketing instance and enter a ticket number.

        Raises:
            TicketIdentifierNotFound: If the instance identifier doesn't match any
                in the config.

        Returns:
            tuple[TicketingInstance, str]: The selected ticketing instance and ticket
                ID.
        """
        ticket_conf = self._config.get_ticketing_config()
        logger.info("Please enter the prefix of the ticket instance:")
        logger.info("PREFIX --- INSTANCE URL --- DESCRIPTION")
        for id, conf in ticket_conf.items():
            logger.info(f"{id} --- {conf.url} --- {conf.description or ''}")
        
        input_id = input("> ")

        ticket_instance_conf = ticket_conf.get(input_id)
        if not ticket_instance_conf: 
            raise TicketIdentifierNotFound(f"No prefix matches: {input_id}")

        ticketing_instance = TicketingInstanceFactory.create(
            ticket_instance_conf.class_name,
            ticket_instance_conf.url,
            ticket_instance_conf.api_key,
            ticket_instance_conf.username
        )

        logger.info("Please enter your ticket number:")
        input_num = input("> ")

        ticket_id = f"{ticket_instance_conf.project_prefix or ''}{input_num}"

        return ticketing_instance, ticket_id
