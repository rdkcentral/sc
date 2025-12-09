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

from sc.review.exceptions import TicketIdentifierNotFound
from ..ticketing_instances import JiraInstance, RedmineInstance
from ..core.ticketing_instance import TicketingInstance

from jira import JIRA
from redminelib import Redmine

class TicketingInstanceFactory:
    @classmethod
    def create(
        cls,
        provider: str,
        url: str,
        token: str,
        auth_type: str = "token",
        username: str | None = None,
        cert: str | None = None
    ) -> TicketingInstance:
        if provider == "redmine":
            instance = Redmine(
                url,
                key=token
            )
            return RedmineInstance(instance)

        elif provider == "jira":
            options = {}
            if cert:
                options["client_cert"] = cert
            if auth_type == "token":
                instance = JIRA(
                    server=url,
                    token_auth=token,
                    options=options
                )
            elif auth_type == "basic":
                instance = JIRA(
                    server=url,
                    basic_auth=(username, token),
                    options=options
                )
            return JiraInstance(instance)
        else:
            raise TicketIdentifierNotFound(
                f"Provider {provider} doesn't match any ticketing instance!")
