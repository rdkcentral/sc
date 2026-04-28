import logging

from .review_config import TicketHostCfg

logger = logging.getLogger(__name__)

class Prompter:
    def yn(self, msg: str) -> bool:
        return input(f"{msg} (y/n): ").strip().lower() == 'y'

    def ticket_selection(
            self, ticket_conf: dict[str, TicketHostCfg])-> tuple[str, str]:
        """Prompt the user to select a ticketing instance and enter a ticket number.

        Raises:
            TicketIdentifierNotFound: If the instance identifier doesn't match any
                in the config.

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
