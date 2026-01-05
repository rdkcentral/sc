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
from requests.exceptions import RequestException
from typing import Literal

from jira import JIRA
from jira.exceptions import JIRAError

from ..exceptions import PermissionsError, TicketNotFound
from ..ticket import Ticket
from .ticketing_instance import TicketingInstance

class JiraInstance(TicketingInstance):
    """A class to handle operations on Jira tickets.

    Args:
        url (str): URL of Jira instance.
        token (str): Token to authenticate with.
        auth_type (str): Either token for token auth or basic for basic auth. Basic
            auth takes an email and password, token takes a token.
        username (str): The username if using basic auth.
        cert (str): The cert.

    Raises:
        TicketingInstanceUnreachable: If the ticketing instance cannot be connected to.
    """

    def __init__(
            self,
            url: str,
            token: str,
            auth_type: Literal["token", "basic"] = "token",
            username: str | None = None,
            cert: str | None = None
        ):
            self.url = url
            options = {}
            if cert:
                options["client_cert"] = cert
            if auth_type == "token":
                self._instance = JIRA(
                    server=url,
                    token_auth=token,
                    options=options
                )
            elif auth_type == "basic":
                self._instance = JIRA(
                    server=url,
                    basic_auth=(username, token),
                    options=options
                )

    @property
    def engine(self) -> str:
        return 'jira'

    def validate_connection(self) -> bool:
        """Check that the Jira instance and credentials are valid."""
        try:
            self._instance.myself()
            return True

        except JIRAError as e:
            if e.status_code in (401, 403):
                raise ConnectionError("Invalid Jira credentials or insufficient permissions.") from e
            raise ConnectionAbortedError(f"Jira API error: HTTP {e.status_code}") from e

        except RequestException as e:
            raise ConnectionError("Unable to reach Jira server.") from e

    def read_ticket(self, ticket_id: str) -> Ticket:
        """Reads the contents of the ticket and puts the dictionary in to contents

        Args:
            ticket_id (str): The id of the ticket to read. Defaults to None
        """
        try:
            issue = self._instance.issue(ticket_id)
        except JIRAError as e:
            if 'permission' in e.text:
                raise PermissionsError(
                    e.url, 'Please contact the dev-support team')
            else:
                raise TicketNotFound(e.url)

        f = issue.fields
        assignee = getattr(f.assignee, "name", None)
        author = getattr(f.reporter, "name", None)

        comments = getattr(f.comment, "comments", None)

        status = f.status.name
        title = f.summary

        versions = getattr(f, "fixVersions", [])
        target_version = ", ".join(v.name for v in versions)

        ticket_url = f'{self.url}/browse/{ticket_id}'

        return Ticket(
            url=ticket_url,
            assignee=assignee,
            author=author,
            comments=comments,
            id=ticket_id,
            status=status,
            target_version=target_version,
            title=title,
        )

    def add_comment_to_ticket(self, ticket_id: str, comment_message: str):
        """Adds a comment to the ticket

        Args:
            comment_message (str): The body of the comment
            ticket_id (str, optional): The ticket id to add the comment to. Defaults to None.
        """
        comment = self._convert_from_html(comment_message)
        return self._instance.add_comment(ticket_id, comment=comment)

    def _convert_from_html(self, string: str) -> str:
        string = string.replace('<p style="', '{')
        string = string.replace('">', '}')
        string = string.replace('</p>', '{color}')
        string = string.replace('<pre>', '{noformat}')
        string = string.replace('</pre>', '{noformat}')
        return string
