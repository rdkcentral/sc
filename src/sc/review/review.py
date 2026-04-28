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

from .exceptions import TicketIdentifierNotFound
from .git_host_service import GitHostService
from .models import CodeReview, CommentData, RepoInfo
from .prompter import Prompter
from .repo_source import RepoSource
from .ticket_service import TicketService

logger = logging.getLogger(__name__)

class Review:
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
        try:
            identifier, ticket_num = self._ticket_service.match_branch(
                self.repo_source.active_branch)
        except TicketIdentifierNotFound as e:
            logger.warning(e)
            identifier, ticket_num = self._ticket_service.prompt_ticket()

        ticket_instance, ticket = self._ticket_service.resolve(identifier, ticket_num)

        comments = []
        for repo_info in self.repo_source.get_repos():
            create_cr_url = None
            try:
                cr = self._git_service.get_git_review_data(repo_info)
            except RuntimeError as e:
                logger.error(e)
                create_cr_url = self._git_service.get_create_cr_url(repo_info)

            comments.append(self._create_comment_data(repo_info, cr, create_cr_url))

        logger.info(f"Ticket URL: [{ticket.url if ticket else 'None'}]")
        logger.info("Ticket info: \n")
        print(self._generate_combined_terminal_comment(comments))
        print()

        if self._prompter.yn("Update ticket?"):
            ticket_comment = self._generate_combined_ticket_comment(comments)
            self._ticket_service.update(ticket_instance, ticket.id, ticket_comment)

    def _create_comment_data(
            self,
            repo_info: RepoInfo,
            cr: CodeReview | None,
            create_cr_url: str | None) -> CommentData:
        review_status = str(cr.status) if cr.status else "Not Created"
        review_url = cr.url if cr.url else None

        return CommentData(
            branch=repo_info.branch,
            directory=repo_info.directory,
            remote_url=repo_info.remote_url,
            review_status=review_status,
            review_url=review_url,
            create_cr_url=create_cr_url,
            commit_sha=repo_info.commit_sha,
            commit_author=repo_info.commit_author,
            commit_date=repo_info.commit_date,
            commit_message=repo_info.commit_message
        )

    def _generate_combined_terminal_comment(self, comments: list[CommentData]) -> str:
        return "\n\n".join(c.to_terminal() for c in comments)

    def _generate_combined_ticket_comment(self, comments: list[CommentData]) -> str:
        return "\n\n".join(c.to_ticket() for c in comments)

