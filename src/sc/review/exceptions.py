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

class ReviewException(Exception):
    pass

class TicketNotFound(ReviewException):
    """Raised when a ticket cannot be found.

    Args:
        ticket_url (str): URL of the ticket not found.
    """
    def __init__(self, ticket_url: str):
        super().__init__(f'Ticket not found at url: {ticket_url}')

class TicketingInstanceUnreachable(ReviewException):
    """Raised when a ticketing instance is unreachable.

    Args:
        instance_url (str): The URL of the unreachable instance.
        additional_info (str): Info on why the instance was unreachable, defaults to ''.
    """
    def __init__(self, instance_url: str, additional_info: str = ''):
        super().__init__(
            f'Ticketing instance at {instance_url} is unreachable: {additional_info}'
        )

class PermissionsError(ReviewException):
    """Raised when permission is denied.

    Args:
        resource (str): The resource access is denied to.
        resolution_message (str): Additional info about access denial, defaults to ''.
    """
    def __init__(self, resource: str, resolution_message: str = ''):
        super().__init__(
            f'You do not have permission to access {resource}.\n{resolution_message}'
        )

class TicketIdentifierNotFound(ReviewException):
    """Raised when ticket ID isn't found in the config.
    """
    pass

class RemoteUrlNotFound(ReviewException):
    """Raised when remote url matches no patterns in the config.
    """
