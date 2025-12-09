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

from json.decoder import JSONDecodeError
from requests import post
from requests.exceptions import InvalidURL, RequestException

from jira import JIRA
from jira.exceptions import JIRAError

from ..exceptions import PermissionsError, TicketingInstanceUnreachable, TicketNotFound
from ..core.ticket import Ticket
from ..core.ticketing_instance import TicketingInstance

class JiraInstance(TicketingInstance):
    """A class to handle operations on Jira tickets.

    Args:
        url (str): URL of Jira instance.
        password (str): Password to authenticate with.
        cert (str | None): Path to a cert file.

    Common KWargs:
        verify (bool): Whether to use ssl verification. Default True
        extra_setup_options (dict): extra setup options for the jira instance

    Raises:
        TicketingInstanceUnreachable: If the ticketing instance cannot be connected to.
    """

    def __init__(
            self,
            instance: JIRA
        ):
        self._instance = instance

    @property
    def engine(self) -> str:
        return 'jira'

    def validate_connection(self) -> bool:
        """Check that the Jira instance and credentials are valid."""
        try:
            # Simple lightweight call that requires authentication
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
            issue_contents = self._instance.issue(ticket_id).raw['fields']
        except JIRAError as e:
            if 'permission' in e.text:
                raise PermissionsError(
                    e.url, 'Please contact the dev-support team')
            else:
                raise TicketNotFound(e.url)
        try:
            assignee = issue_contents['assignee'].get('name')
        except (KeyError, AttributeError):
            assignee = None
        author = issue_contents['creator'].get('name')
        try:
            comments = issue_contents['comment'].get('comments')
        except (KeyError, AttributeError):
            comments = None
        status = issue_contents['status'].get('name')
        target_version = ', '.join([version.get('name') for version in issue_contents.get('fixVersions')])
        title = issue_contents.get('summary', '')
        ticket_url = f'{self.url}/browse/{ticket_id}'
        ticket = Ticket(ticket_url,
                        assignee=assignee,
                        author=author,
                        comments=comments,
                        contents=issue_contents,
                        id=ticket_id,
                        status=status,
                        target_version=target_version,
                        title=title,
                        url=ticket_url)
        return ticket

    def add_comment_to_ticket(self, ticket_id: str, comment_message: str):
        """Adds a comment to the ticket

        Args:
            comment_message (str): The body of the comment
            ticket_id (str, optional): The ticket id to add the comment to. Defaults to None.
        """
        try:
            comment = self._convert_from_html(comment_message)
            ticket = self._instance.add_comment(ticket_id, comment=comment)
            ticket = self._instance.up
        except TicketNotFound:
            # Some workflows do not accept the above method for adding a comment as it technically rewrites the whole ticket
            try:
                # Try a post request directly to the add comment REST api instead
                content = {'body': comment}
                post('{url}/rest/api/2/issue/{ticket_id}/comment'.format(
                    url=self.url, ticket_id=ticket_id),
                    json=content,
                    headers={
                        "Authorization": f"Bearer {self._credentials.get('password')}"
                    },
                    cert=self._default_jira_setup.get('client_cert'),
                    proxies=self._instance._session.proxies)
                ticket = self.read_ticket(ticket_id)
            except RequestException:
                raise TicketNotFound(self.url)
        return ticket

    def _update_ticket(self, ticket_id: str, **kwargs):
        """Updates the ticket with the new value for the fields based on the kwargs

        Args:
            ticket_id (str): The id of the ticket to update. Defaults to None.
        """
        try:
            self._instance.issue(ticket_id).update(**kwargs)
        except JIRAError as e:
            raise TicketNotFound(e.url)
        ticket = self.read_ticket(ticket_id)
        return ticket

    def _convert_from_html(self, string: str) -> str:
        string = string.replace('<p style="', '{')
        string = string.replace('">', '}')
        string = string.replace('</p>', '{color}')
        string = string.replace('<pre>', '{noformat}')
        string = string.replace('</pre>', '{noformat}')
        return string
