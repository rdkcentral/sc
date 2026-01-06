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
import urllib3

from redminelib import Redmine
from redminelib.resources import Issue
from redminelib.exceptions import BaseRedmineError, ForbiddenError, ResourceNotFoundError, AuthError
from requests.exceptions import RequestException, SSLError

from sc.review.exceptions import PermissionsError, TicketingInstanceUnreachable, TicketNotFound
from sc.review.ticket import Ticket
from .. import TicketingInstance

class RedmineInstance(TicketingInstance):
    """
    A class to handle operations on Redmine tickets.
    """

    def __init__(
            self,
            url: str,
            token: str,
            verify_ssl: bool = False
        ):
        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self._instance = Redmine(
            url,
            key=token,
            requests={'verify': verify_ssl}
        )
        self._validate_connection()

    @property
    def engine(self) -> str:
        return 'redmine'

    def read_ticket(self, ticket_id: str) -> Ticket:
        """Read the information from a ticket and put its contents in this object contents dict

        Args:
            ticket_id (str): The ticket number to read.
        Raises:
            TicketNotFound: Ticket not found on the redmine instance
            PermissionsError: User does not have permission to access the ticket on the instances
            TicketingInstanceUnreachable: The redmine instance is unreachable
        """
        ticket_url = self._instance.url + '/issues/' + ticket_id
        try:
            issue: Issue = self._instance.issue.get(ticket_id, include=['journals'])
        except ResourceNotFoundError as e:
            raise TicketNotFound(ticket_url) from e
        except (AuthError, ForbiddenError) as e:
            raise PermissionsError(
                ticket_url,
                'Please contact the dev-support team') from e
        except SSLError as e:
            raise TicketingInstanceUnreachable(
                ticket_url,
                additional_info=''.join(str(arg) for arg in e.args))

        issue_contents = issue.__dict__

        author = issue_contents.get("author", {}).get("name")
        assignee = issue_contents.get("assigned_to", {}).get("name")
        comments = issue_contents.get("journals")
        status = issue_contents.get("status", {}).get("name")
        target_version = issue_contents.get("fixed_version", {}).get("name")
        title = issue_contents.get("subject")

        return Ticket(
            ticket_url,
            author=author,
            assignee=assignee,
            comments=comments,
            id=ticket_id,
            status=status,
            title=title,
            target_version=target_version
        )

    def add_comment_to_ticket(self, ticket_id: str, comment_message: str):
        """Add a comment to a ticket on the redmine instance

        Args:
            comment_message (str): The message to add as a comment
            ticket_id (str): The ticket number to add the comment to.
        """
        self._update_ticket(ticket_id, notes=self._convert_html_colours(comment_message))

    def _update_ticket(self, ticket_id: str, **kwargs):
        """Writes the changed fields from the kwargs, back to the ticket

        Raises:
            TicketNotFound: Ticket not found on the redmine instance
            PermissionsError: User does not have permission to access the ticket on the instances
            TicketingInstanceUnreachable: The redmine instance is unreachable
        """
        issue_url = f'{self._instance.url}/issues/{ticket_id}'
        try:
            self._instance.issue.update(ticket_id, **kwargs)
        except ResourceNotFoundError as exception:
            raise TicketNotFound(issue_url) from exception
        except ForbiddenError as exception:
            raise PermissionsError(
                issue_url, 'Please contact the dev-support team') from exception
        except SSLError as exception:
            raise TicketingInstanceUnreachable(
                issue_url,
                additional_info=''.join(str(arg) for arg in exception.args))
        ticket = self.read_ticket(ticket_id)
        return ticket

    def _validate_connection(self) -> bool:
        """Check if the Redmine instance and API key are valid.

        Raises:
            ConnectionError: If the connection is invalid.

        Returns:
            bool: True if connection is valid.
        """
        try:
            self._instance.auth()
            return True

        except (AuthError, ForbiddenError) as e:
            raise ConnectionError(
                "Invalid Redmine API key or insufficient permissions for "
                f"{self._instance.url}."
            ) from e

        except BaseRedmineError as e:
            raise ConnectionError(
                f"Redmine API error at {self._instance.url}: {e}") from e

        except RequestException as e:
            raise ConnectionError(
                f"Failed to reach Redmine server at {self._instance.url}") from e

    def _convert_html_colours(self, string: str) -> str:
        """Convert a html colour tags to redmine formatted colour tags.

        Args:
            string (str): html formatted string.

        Returns:
            str: Input string with html colour tags converted to redmine colour tags.
        """
        string = string.replace('<p style="', r'%{')
        string = string.replace('">', '}')
        string = string.replace('</p>', r'%')
        return string
