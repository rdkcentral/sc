import unittest
from unittest.mock import MagicMock

from sc.services.tickets.ticket_config import TicketHostConfig, TicketHostModel


class TestTicketHostConfig(unittest.TestCase):
    def setUp(self):
        self.config_manager = MagicMock()
        self.ticket_config = TicketHostConfig(self.config_manager)

    def test_get_identifiers_returns_only_ticketing_instances(self):
        self.config_manager.get_config.return_value = {
            "git_instances": {"github.com": {}},
            "ticketing_instances": {
                "ABC": {
                    "url": "https://tickets.example.test",
                    "provider": "jira",
                    "api_key": "token",
                }
            },
        }

        self.assertEqual(self.ticket_config.get_identifiers(), {"ABC"})

    def test_get_is_case_insensitive(self):
        self.config_manager.get_config.return_value = {
            "ticketing_instances": {
                "ABC": {
                    "url": "https://tickets.example.test",
                    "provider": "jira",
                    "api_key": "token",
                }
            }
        }

        self.assertEqual(
            self.ticket_config.get("abc"),
            TicketHostModel(
                url="https://tickets.example.test",
                provider="jira",
                api_key="token",
            ),
        )

    def test_write_updates_ticketing_instances_section(self):
        model = TicketHostModel(
            url="https://tickets.example.test",
            provider="jira",
            api_key="token",
        )

        self.ticket_config.write("ABC", model)

        self.config_manager.update_config.assert_called_once_with(
            "ticketing_instances",
            {
                "ABC": {
                    "url": "https://tickets.example.test",
                    "provider": "jira",
                    "api_key": "token",
                    "auth_type": "token",
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
