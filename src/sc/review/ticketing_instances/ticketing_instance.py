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

from abc import ABC, abstractmethod

from ..ticket import Ticket

class TicketingInstance(ABC):
    """
    A class to handle the ticket(s) that the source control commands are
    operating on.
    """
    @property
    @abstractmethod
    def engine(self) -> str:
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
    def add_comment_to_ticket(self, ticket_id: str, comment_message: str):
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
