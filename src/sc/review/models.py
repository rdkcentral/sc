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
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

@dataclass
class Ticket:
    url: str
    author: str | None = None
    assignee: str | None = None
    comments: str | None = None
    id: str | None = None
    status: str | None = None
    target_version: str | None = None
    title: str | None = None

class CRStatus(str, Enum):
    OPEN = "Open"
    CLOSED = "Closed"
    MERGED = "Merged"

    def __str__(self):
        return self.value

@dataclass
class CodeReview:
    url: str
    status: CRStatus

@dataclass
class RepoInfo:
    branch: str
    directory: str | Path
    remote_url: str
    commit_sha: str
    commit_author: str
    commit_date: datetime
    commit_message: str
