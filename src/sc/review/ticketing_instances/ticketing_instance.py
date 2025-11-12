#!/usr/bin/env python3
from abc import ABC, abstractmethod
from os.path import abspath, exists

from .ticket import Ticket


class TicketingInstance(ABC):
    """
    A class to handle the ticket(s) that the source control commands are
    operating on.
    """

    @abstractmethod
    def __init__(self, url: str, **kwargs):
        self._credentials = {}
        self._url = url
        if 'username' and 'password' in kwargs.keys():
            self.set_credentials(kwargs.get('username'), kwargs.get('password'))

    @property
    def url(self):
        return self._url

    @property
    @abstractmethod
    def engine(self) -> str:
        pass

    @abstractmethod
    def create_ticket(self) -> Ticket:
        """Abstract Method:
        Create a ticket on the ticketing instance.
        Read it's contents return the new ticket object

        Returns:
            ticket (Ticket): The newly created ticket object
        """
        # create ticket
        # read tickets contents
        # return ticket object
        pass

    @abstractmethod
    def read_ticket(self, ticket_id: str) -> Ticket:
        """Abstract Method:
        Read the ticket and return it as a ticket object

        Args:
            ticket_id (str): The id of the ticket to update.
        Returns:
            ticket (Ticket): ticket object.
        """
        pass

    @abstractmethod
    def update_ticket(self, ticket_id, **kwargs) -> Ticket:
        """Abstract Method:
        Updates the contents dictionary.
        Should update the tickets with the changes in the kwargs.
        Reads the updated ticket and returns it as a new ticket object

        Args:
            ticket_id (str): The id of the ticket to update.
        Returns:
            ticket (Ticket): New ticket object with update applied.
        """
        pass

    @abstractmethod
    def add_comment_to_ticket(self, ticket_id: str,
                              comment_message: str) -> Ticket:
        """Abstract Method:
        Adds a comment to the ticket on the ticketing instance.
        Reads the new ticket with the new comment.
        Returns new ticket object with comment added

        Args:
            ticket_id (str): The id of the ticket to update.
            comment_message (str): The comment to add to the ticket.

        Returns:
            ticket (Ticket): New ticket object with comment added
        """
        pass

    @abstractmethod
    def delete_ticket(self, ticket_id: str) -> bool:
        """Abstract Method:
        Should remove the ticket from the instance

        Args:
            ticket_id (str, optional): The id of the ticket to remove.

        Returns:
            result (bool): True if ticket removed successfully.
        """
        pass

    def set_credentials(self, username: str, password: str):
        """Set the username and password for in the credentials dictionary.

        Args:
            username (str): Username of the user to login to the ticketing instance with
            password (str): Password/API key of the user to login to the ticketing instance with
        """
        self._credentials = {'username': username, 'password': password}

    def _version_check(self, required_version: str,
                       instance_version: str) -> str:
        """Compares the versions.

        Args:
            required_version (str): Version to compare against
            instance_version (str): Version to check

        Returns:
            str: (later, same, ealier) depending on the comparison of the versions
        """
        if required_version.count('.') < 2:
            required_version += '.0.0'
        if instance_version.count('.') < 2:
            instance_version += '.0.0'
        required_major, required_minor, required_bug = required_version.split(
            '.')
        instance_major, instance_minor, instance_bug = instance_version.split(
            '.')
        if instance_version == required_version:
            return 'same'
        if int(instance_major) > int(required_major):
            return 'later'
        elif int(instance_major) == int(required_major):
            if int(instance_minor) > int(required_minor):
                return 'later'
            elif int(instance_minor) == int(required_minor):
                if int(instance_bug) > int(required_bug):
                    return 'later'
        return 'earlier'
