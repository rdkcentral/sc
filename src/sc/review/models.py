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
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from urllib import parse

class CRStatus(str, Enum):
    OPEN = "Open"
    CLOSED = "Closed"
    MERGED = "Merged"

    def __str__(self):
        return self.value

@dataclass
class CodeReview:
    url: str | None
    status: CRStatus | None
    create_url: str | None

    def exists(self) -> bool:
        return self.url is not None

@dataclass
class RepoInfo:
    branch: str
    directory: str | Path
    remote_url: str
    commit_sha: str
    commit_author: str
    commit_date: datetime
    commit_message: str

    @property
    def repo_slug(self) -> str:
        """Return the repository slug (e.g. "org/repo") from a remote url."""
        if self.remote_url.startswith("git@"):
            slug = self.remote_url.split(":", 1)[1]
        else:
            slug = parse.urlparse(self.remote_url).path.lstrip("/")

        slug = slug.strip("/")

        if slug.endswith(".git"):
            slug = slug[:-4]

        return slug

@dataclass
class CommentData:
    branch: str
    directory: str | Path
    remote_url: str
    ticket_url: str
    ticket_title: str
    code_review: CodeReview
    commit_sha: str
    commit_author: str
    commit_date: datetime
    commit_message: str

    @property
    def has_code_review(self) -> bool:
        return self.review_url is not None

    def to_terminal(self) -> str:
        """Generate the information for one repo to be displayed in the terminal.

        Returns:
            str: Information from one repo to be displayed in the terminal.
        """
        def c(code, text):
            return f"\033[{code}m{text}\033[0m"

        header = [
            f"Branch: [{self.branch}]",
            f"Directory: [{self.directory}]",
            f"Git: [{self.remote_url}]",
        ]

        ticket_link = f"Ticket: [{c('34', self.ticket_url)}]"
        ticket_title = f"Ticket Title: [{c('34', self.ticket_title)}]"
        if self.code_review.exists():
            review_status = f"Review Status: [{c('32', self.code_review.status)}]"
            review_link = f"Review URL: [{c('32', self.code_review.url)}]"
        else:
            review_status = f"Review Status: [{c('31', 'Not Created')}]"
            review_link = f"Create Review URL: [{c('33', self.code_review.create_url)}]"

        review = [ticket_link, ticket_title, review_status, review_link]

        commit = (
            f"Last Commit: [{self.commit_sha}]",
            f"Author: [{self.commit_author}]",
            f"Date: [{self.commit_date}]",
            "",
            f"{self.commit_message}"
        )

        return "\n".join([*header, "", *review, "", *commit])

    def to_ticket(self) -> str:
        """Generate the information for one repo formatted for a ticket comment.

        Returns:
            str: A formatted ticket comment.
        """
        header = [
            f"Branch: [{self.branch}]",
            f"Directory: [{self.directory}]",
            f"Git: [{self.remote_url}]",
        ]

        ticket_link = f"Ticket: [{self.ticket_url}]"
        ticket_title = f"Ticket Title: [{self.ticket_title}]"
        if self.review_url:
            review_status = f"Review Status: [{self.review_status}]"
            review_link = f"Review URL: [{self.review_url}]"
        else:
            review_status = f"Review Status: [{self.review_status}]"
            review_link = f"Create Review URL: [{self.create_cr_url}]"

        review = [ticket_link, ticket_title, review_status, review_link]

        commit = (
            "<pre>",
            f"Last Commit: [{self.commit_sha}]",
            f"Author: [{self.commit_author}]",
            f"Date: [{self.commit_date}]",
            "",
            f"{self.commit_message}",
            "</pre>"
        )

        return "\n".join([*header, "", *review, "", *commit])
