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

import logging

from .git_host_service import GitHostService
from .models import CodeReview, CommentData, RepoInfo
from sc.prompter import Prompter
from .repo_source import RepoSource
from sc.exceptions import ScError
from ..services.tickets import Ticket
from ..services.tickets.ticket_service import TicketService

logger = logging.getLogger(__name__)

class TicketUpdater:
    def __init__(
            self,
            repo_source: RepoSource,
            ticket_service: TicketService | None = None,
            git_service: GitHostService | None = None,
            prompter: Prompter | None = None
        ):
        self.repo_source = repo_source
        self._ticket_service = ticket_service or TicketService()
        self._git_service = git_service or GitHostService()
        self._prompter = prompter or Prompter()

    def run(self):
        ticket = self._get_ticket()
        repo_infos = self.repo_source.get_repos()

        while True:
            comments = self._get_comments(ticket, repo_infos)

            logger.info(f"Ticket URL: [{ticket.url if ticket else 'None'}]")
            logger.info("Ticket info: \n")
            print(self._generate_combined_terminal_comment(comments))
            print()

            if self._code_review_missing(comments):
                choice = self._prompter.choice(
                    "Update ticket? [y/n/r - refresh code reviews]",
                    ("y", "n", "r")
                )
            else:
                choice = self._prompter.choice("Update ticket? [y/n]", ("y", "n"))

            if choice == "y":
                ticket_comment = self._generate_combined_ticket_comment(comments)
                ticket.add_comment(ticket_comment)
            elif choice == "r":
                continue

            return

    def _get_ticket(self) -> Ticket:
        """Get ticket and ticketing instance from branch, on failure prompt the user
        to manually enter.
        """
        try:
            ticket = self._ticket_service.get_ticket_from_branch(self.repo_source.active_branch)
        except ScError as e:
            logger.warning(e)
            ticket = self._ticket_service.prompt_ticket()

        while True:
            print(ticket.to_terminal())
            if self._prompter.yn("Use this ticket?"):
                return ticket

            ticket = self._ticket_service.prompt_ticket()

    def _get_comments(self, ticket: Ticket, repo_infos: list[RepoInfo]) -> list[CommentData]:
        comments = []

        for repo_info in repo_infos:
            cr = self._git_service.get_code_review_data(repo_info)
            comments.append(self._create_comment_data(repo_info, ticket, cr))

        return comments

    def _create_comment_data(
            self,
            repo_info: RepoInfo,
            ticket: Ticket,
            cr: CodeReview) -> CommentData:
        return CommentData(
            branch=repo_info.branch,
            directory=repo_info.directory,
            remote_url=repo_info.remote_url,
            ticket_url=ticket.url,
            ticket_title=ticket.title,
            code_review=cr,
            commit_sha=repo_info.commit_sha,
            commit_author=repo_info.commit_author,
            commit_date=repo_info.commit_date,
            commit_message=repo_info.commit_message
        )

    def _generate_combined_terminal_comment(self, comments: list[CommentData]) -> str:
        return f"\n{'-'*100}\n".join(c.to_terminal() for c in comments)

    def _generate_combined_ticket_comment(self, comments: list[CommentData]) -> str:
        return f"\n{'-'*100}\n".join(c.to_ticket() for c in comments)

    def _code_review_missing(self, comments: list[CommentData]) -> bool:
        return any(not c.has_code_review for c in comments)
