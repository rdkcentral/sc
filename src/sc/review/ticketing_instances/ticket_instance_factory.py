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
from typing import Literal

from sc.review.exceptions import TicketIdentifierNotFound
from .instances import JiraInstance, RedmineInstance
from .ticketing_instance import TicketingInstance

class TicketingInstanceFactory:
    @classmethod
    def create(
        cls,
        provider: str,
        url: str,
        token: str,
        auth_type: Literal["token", "basic"] = "token",
        username: str | None = None,
        cert: str | None = None
    ) -> TicketingInstance:
        """Ticketing instance factory method.

        Args:
            provider (str): Which ticketing provider. jira or redmine supported.
            url (str): URL to ticketing provider.
            token (str): The token or password for the provider.
            auth_type (Literal["token", "basic"], optional): Auth method.
                Defaults to "token".
            username (str | None, optional): Username for basic auth. Defaults to None.
            cert (str | None, optional): Path to a cert. Defaults to None.

        Raises:
            TicketIdentifierNotFound: Provider isn't supported.
            ConnectionError: Fail to connect or validate with provider.

        Returns:
            TicketingInstance
        """
        if provider == "redmine":
            return RedmineInstance(
                url,
                token=token
            )
        elif provider == "jira":
            return JiraInstance(
                url,
                token=token,
                auth_type=auth_type,
                username=username,
                cert=cert
            )
        else:
            raise TicketIdentifierNotFound(
                f"Provider {provider} is not supported."
                " Supported providers are: redmine, jira"
            )
