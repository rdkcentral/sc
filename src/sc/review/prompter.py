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

from .review_config import TicketHostModel

logger = logging.getLogger(__name__)

class Prompter:
    def yn(self, msg: str) -> bool:
        return input(f"{msg} (y/n): ").strip().lower() == 'y'

    def ticket_selection(
            self, ticket_conf: dict[str, TicketHostModel])-> tuple[str, str]:
        """Prompt the user to select a ticketing instance and enter a ticket number.

        Returns:
            tuple[str, str]: The selected ticketing instance identifier and ticket
                number.
        """
        logger.info("Please enter the prefix of the ticket instance:")
        logger.info("PREFIX --- INSTANCE URL --- DESCRIPTION")
        for id, conf in ticket_conf.items():
            logger.info(f"{id} --- {conf.url} --- {conf.description or ''}")

        input_id = input("> ")
        while input_id not in ticket_conf.keys():
            logger.info(f"Prefix {input_id} not found in instances.")
            input_id = input("> ")

        logger.info("Please enter your ticket number:")
        input_num = input("> ")

        return input_id, input_num
