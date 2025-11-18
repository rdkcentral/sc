#!/usr/bin/env python3

from json.decoder import JSONDecodeError
import os
from requests import post
from requests.exceptions import InvalidURL, RequestException
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

from jira import JIRA
from jira.exceptions import JIRAError

from ..exceptions import PermissionsError, TicketingInstanceUnreachable, TicketNotFound
from .ticket import Ticket
from .ticketing_instance import TicketingInstance


class JiraInstance(TicketingInstance):
    """A class to handle operations on Jira tickets.

    Args:
            url (str): URL of Jira instance.
            password (str): Password to authenticate with.

    Common KWargs:
        verify (bool): Whether to use ssl verification. Default True
        extra_setup_options (dict): extra setup options for the jira instance

    Raises:
        TicketingInstanceUnreachable: If the ticketing instance cannot be connected to.
    """

    def __init__(self, url: str, password: str, **kwargs):
        self._default_jira_setup = {
            'server': '',
            'verify': True,
            'rest_api_version': '2',
        }
        super().__init__(url, password=password, **kwargs)
        self._default_jira_setup['server'] = url
        self._default_jira_setup['verify'] = kwargs.get('verify', True)
        if isinstance(kwargs.get('extra_setup_options'), dict):
            self._default_jira_setup.update(kwargs.get('extra_setup_options'))
        # If the user does not want to use SSL verification disable the warnings about it being insecure.
        if self._default_jira_setup.get('verify') is False:
            disable_warnings(InsecureRequestWarning)
        # 9.0.0. is an arbitrary version that hasn't been release yet
        # Jira is currently readying version 3 of the api so we should be ready for it
        if kwargs.get('version') and self._version_check(
                '9.0.0', kwargs.get('version', '0.0.0')) in ('same', 'later'):
            self._default_jira_setup['rest_api_version'] = '3'
        if kwargs.get('cert') or kwargs.get('certificate'):
            self._set_cert(kwargs.get('cert', kwargs.get('certificate')))
        try:
            self._instance = JIRA(
                options=self._default_jira_setup,
                token_auth=self._credentials.get('password'),
                proxies=kwargs.get('proxies', None))
        except AttributeError as e:
            raise TicketingInstanceUnreachable(url,
                                               additional_info=''.join(
                                                   arg for arg in e.args))
        except JIRAError as e:
            raise TicketingInstanceUnreachable(e.url,
                                               additional_info=e.status_code)
        except JSONDecodeError:
            raise TicketingInstanceUnreachable(
                url, additional_info='Certificate Response Error')
        except InvalidURL as e:
            raise TicketingInstanceUnreachable(url,
                                               additional_info=''.join(
                                                   arg for arg in e.args))

    def __del__(self):
        if self._default_jira_setup.get('client_cert'):
            os.remove(self._default_jira_setup.get('client_cert'))

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

    def create_ticket(self, project_key: str, issue_type: str, title: str,
                      **kwargs):
        """Creates a ticket on the Jira instance

        Args:
            project_key (str): The projects key on th Jira instance
            issue_type (str): The type of issue to raise
            titlr (str): Title of the ticket to raise
        """
        project_dict = {'project': {'key': project_key}}
        kwargs.update(project_dict)
        kwargs.update({'issuetype': issue_type, 'summary': title})
        new_issue_id = self._instance.create_issue(fields=kwargs).key
        ticket = self.read_ticket(new_issue_id)
        return ticket

    def read_ticket(self, ticket_id: str) -> Ticket:
        """Reads the contents of the ticket and puts the dictionary in to contents

        Args:
            ticket_id (str): The id of the ticket to read. Defaults to None
        """
        try:
            issue_contents = self._instance.issue(ticket_id).raw['fields']
        except JIRAError as e:
            if 'permission' in e.text:
                raise PermissionsError(e.url,
                                       'Please contact the dev-support team')
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
        ticket_url = '{instance_url}/browse/{ticket_id}'.format(
            instance_url=self.url, ticket_id=ticket_id)
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

    def update_ticket(self, ticket_id: str, **kwargs):
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

    def add_comment_to_ticket(self, ticket_id: str, comment_message: str):
        """Adds a comment to the ticket

        Args:
            comment_message (str): The body of the comment
            ticket_id (str, optional): The ticket id to add the comment to. Defaults to None.
        """
        try:
            comment = self._convert_from_html(comment_message)
            ticket = self.update_ticket(ticket_id, comment=comment)
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


    def _convert_from_html(self, string: str) -> str:
        string = string.replace('<p style="', '{')
        string = string.replace('">', '}')
        string = string.replace('</p>', '{color}')
        string = string.replace('<pre>', '{noformat}')
        string = string.replace('</pre>', '{noformat}')
        return string

    def delete_ticket(self, ticket_id: str):
        """Revoves the ticket from the Jira instance

        Args:
            ticket_id (str, optional): The id of the ticket to delete. Defaults to None.
        """
        self._instance.issue(ticket_id).delete()

    def _set_cert(self, cert_path):
        cert = self._get_cert(cert_path)
        self._default_jira_setup['client_cert'] = cert

    def _get_cert(self, cert_path):
        cert_file = self._get_file(cert_path,
                                   output_location='/tmp/',
                                   obfuscate=True)
        return cert_file
