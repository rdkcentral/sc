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

@dataclass
class Ticket:
    url: str
    author: str | None = None
    assignee: str | None = None
    comments: str | None = None
    id: str | None = None
    status: str | None = None
    target_version: str | None = None
    title: str | None = None

class CRStatus(str, Enum):
    OPEN = "Open"
    CLOSED = "Closed"
    MERGED = "Merged"

    def __str__(self):
        return self.value

@dataclass
class CodeReview:
    url: str
    status: CRStatus

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
    review_status: str
    review_url: str | None
    create_cr_url: str | None
    commit_sha: str
    commit_author: str
    commit_date: datetime
    commit_message: str

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
        if self.review_url:
            review_status = f"Review Status: [{c('32', self.review_status)}]"
            review_link = f"Review URL: [{c('32', self.review_url)}]"
        else:
            review_status = f"Review Status: [{c('31', self.review_status)}]"
            review_link = f"Create Review URL: [{c('33', self.create_cr_url)}]"

        review = [ticket_link, review_status, review_link]

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
        if self.review_url:
            review_status = f"Review Status: [{self.review_status}]"
            review_link = f"Review URL: [{self.review_url}]"
        else:
            review_status = f"Review Status: [{self.review_status}]"
            review_link = f"Create Review URL: [{self.create_cr_url}]"

        review = [ticket_link, review_status, review_link]

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
