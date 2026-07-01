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
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ticketing_instances.ticketing_instance import TicketingInstance

@dataclass
class TicketData:
    url: str
    id: str
    author: str | None = None
    assignee: str | None = None
    comments: str | None = None
    status: str | None = None
    target_version: str | None = None
    title: str | None = None

    def to_terminal(self, one_line: bool = False) -> str:
        def c(code, text):
            return f"\033[{code}m{text}\033[0m"

        sections = [
            f"URL: [{c('34', self.url)}]",
            f"ID: [{c('33', self.id)}]",
            f"Title: [{c('33', self.title)}]",
            f"Author: [{c('33', self.author)}]",
            f"Status: [{c('32', self.status)}]"
        ]

        if one_line:
            return " ".join(sections)
        else:
            return "\n".join(sections)

class Ticket:
    def __init__(self, instance: TicketingInstance, ticket_data: TicketData):
        self._instance = instance
        self.data = ticket_data

    @property
    def url(self) -> str:
        return self.data.url

    @property
    def id(self) -> str:
        return self.data.id

    @property
    def title(self) -> str | None:
        return self.data.title

    def add_comment(self, comment: str):
        self._instance.add_comment_to_ticket(self.data.id, comment)

    def to_terminal(self, one_line: bool = False) -> str:
        return self.data.to_terminal(one_line)
