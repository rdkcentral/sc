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
import logging

logger = logging.getLogger(__name__)

class Prompter:
    """Prompts for user input."""
    @staticmethod
    def yn(msg: str) -> bool:
        return input(f"{msg} (y/n): ").strip().lower() == 'y'

    @staticmethod
    def ask(msg: str) -> str:
        return input(f"{msg}\n> ").strip()
