#!/usr/bin/env python3
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

from redminelib import Redmine
from redminelib.exceptions import BaseRedmineError, ForbiddenError, ResourceNotFoundError, AuthError
from requests.exceptions import RequestException, SSLError

from ..exceptions import TicketNotFound, TicketingInstanceUnreachable, PermissionsError
from .ticketing_instance import TicketingInstance
from .ticket import Ticket


class RedmineInstance(TicketingInstance):
    """
    A class to handle operations on Redmine tickets.
    """

    def __init__(self, url, password: str, **kwargs):
        # Only an api key is necessary for Redmine therefore the username can be empty.
        super().__init__(url, password=password, **kwargs)
        # If the user does not want to use SSL verification disable the warnings about it being insecure.
        if kwargs.get('verify') is False:
            disable_warnings(InsecureRequestWarning)
        try:
            self._instance = Redmine(url,
                                     key=self._credentials.get('password'),
                                     requests={
                                         'verify': kwargs.get('verify', True),
                                         'proxies': kwargs.get('proxies', {})
                                     },
                                     version=kwargs.get('version', None))
        except:
            raise TicketingInstanceUnreachable(url)

    @property
    def engine(self) -> str:
        return 'redmine'
    
    def validate_connection(self) -> bool:
        """Check if the Redmine instance and API key are valid."""
        try:
            # Minimal authenticated request
            self._instance.auth()  # redminelib verifies credentials
            return True

        except (AuthError, ForbiddenError) as e:
            ConnectionError("Invalid Redmine API key or insufficient permssions.")
        
        except BaseRedmineError as e:
            raise ConnectionError(f"Redmine API error: {e}")

        except RequestException as e:
            raise ConnectionError("Failed to reach Redmine server.") from e


    def create_ticket(self, project_name: str, title: str, **kwargs) -> Ticket:
        """Create a ticket on the redmine instance

        Args:
            project_name (str): The project to create the ticket under
            title (str): The title of the ticket

        Raises:
            PermissionsError: User does not have permission to access the ticket on the instances
            TicketingInstanceUnreachable: The redmine instance is unreachable
        """
        try:
            new_ticket = self._instance.issue.create(project_id=project_name,
                                                     subject=title,
                                                     **kwargs)
        except (ResourceNotFoundError, SSLError) as exception:
            raise TicketingInstanceUnreachable(
                self.url,
                additional_information=''.join(
                    arg for arg in exception.args)) from exception
        except ForbiddenError as exception:
            raise PermissionsError(
                '{url}/{project}'.format(url=self.url, project=project_name),
                'Please contact the dev-support team')
        ticket_id = new_ticket
        ticket = self.read_ticket(ticket_id)
        return ticket

    def read_ticket(self, ticket_id: str) -> Ticket:
        """Read the information from a ticket and put it's contents in this object contents dict

        Args:
            ticket_id (str): The ticket number to read.
        Raises:
            TicketNotFound: Ticket not found on the redmine instance
            PermissionsError: User does not have permission to access the ticket on the instances
            TicketingInstanceUnreachable: The redmine instance is unreachable
        """
        ticket_url = self.url + '/issues/' + ticket_id
        try:
            issue = self._instance.issue.get(ticket_id, include=['journals'])
        except ResourceNotFoundError as exception:
            raise TicketNotFound(ticket_url) from exception
        except (AuthError, ForbiddenError) as exception:
            raise PermissionsError(
                ticket_url,
                'Please contact the dev-support team') from exception
        except SSLError as exception:
            raise TicketingInstanceUnreachable(
                ticket_url,
                additional_info=''.join(str(arg) for arg in exception.args))
        issue_contents = dict((k, v) for k, v in list(issue))
        author = issue_contents['author'].get('name')
        try:
            assignee = issue_contents['assigned_to'].get('name')
        except KeyError:
            assignee = None
        comments = issue_contents.get('journals')
        status = issue_contents['status'].get('name')
        try:
            target_version = issue_contents['fixed_version'].get('name')
        except KeyError:
            target_version = None
        title = issue_contents.get('subject')
        ticket = Ticket(ticket_url,
                        author=author,
                        assignee=assignee,
                        comments=comments,
                        contents=issue_contents,
                        id=ticket_id,
                        status=status,
                        title=title,
                        url=ticket_url,
                        target_version=target_version)
        return ticket

    def update_ticket(self, ticket_id, **kwargs):
        """Writes the changed fields from the kwargs, back to the ticket

        Raises:
            TicketNotFound: Ticket not found on the redmine instance
            PermissionsError: User does not have permission to access the ticket on the instances
            TicketingInstanceUnreachable: The redmine instance is unreachable
        """
        issue_url = '{url}/issues/{ticket_number}'.format(
            url=self.url, ticket_number=ticket_id)
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

    def add_comment_to_ticket(self, ticket_id: str, comment_message: str) -> None:
        """Add a comment to a ticket on the redmine instance

        Args:
            comment_message (str): The message to add as a comment
            ticket_id (str): The ticket number to add the comment to.
        """
        ticket = self.update_ticket(ticket_id,notes=self._convert_html_colours(comment_message))
        return ticket

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

    def delete_ticket(self, ticket_id: str):
        """Delete a ticket from the redmine instance

        Args:
            ticket_id (str, optional): The ticket number to delete. Defaults to None.

        Raises:
            TicketNotFound: Ticket not found on the redmine instance
            PermissionsError: User does not have permission to access the ticket on the instances
            TicketingInstanceUnreachable: The redmine instance is unreachable
        """
        issue_url = '{url}/issues/{ticket_number}'.format(
            url=self._instance.url, ticket_number=self.ticket_id)
        try:
            self._instance.issue.delete(self.ticket_id)
        except ResourceNotFoundError as exception:
            raise TicketNotFound(issue_url) from exception
        except ForbiddenError as exception:
            raise PermissionsError(
                '{url}/issues/{ticket_number}'.format(url=self._url),
                'Please contact the dev-support team') from exception
        except SSLError as exception:
            raise TicketingInstanceUnreachable(
                issue_url,
                additional_info=''.join(str(arg) for arg in exception.args))
        return True
