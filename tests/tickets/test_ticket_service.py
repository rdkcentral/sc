import unittest
from unittest.mock import Mock, MagicMock, patch

from sc.services.tickets import Ticket, TicketService
from sc.services.tickets.exceptions import TicketIdentifierNotFound

class TestTicketService(unittest.TestCase):
    def setUp(self):
        self.config = MagicMock()
        self.factory = MagicMock()
        self.prompter = MagicMock()

        self.service = TicketService(
            config=self.config,
            factory=self.factory,
            prompter=self.prompter
        )

    def test_get_ticket(self):
        cfg = MagicMock(
            provider="prov",
            url="url",
            api_key="key",
            auth_type="config",
            username="user",
            cert="cert",
            project_prefix="ABC-"
        )
        self.config.get.return_value = cfg

        mock_instance = MagicMock()
        self.factory.create.return_value = mock_instance

        mock_ticket = MagicMock(id="ABC-123")
        mock_instance.read_ticket.return_value = mock_ticket

        ticket = self.service.get_ticket("jira", 123)

        self.factory.create.assert_called_once()
        mock_instance.read_ticket.assert_called_once_with("ABC-123")
        self.assertEqual(ticket, mock_ticket)

    def test_get_ticket_from_branch_success(self):
        self.config.get_identifiers.return_value = ["ABC"]
        expected_ticket = Mock(spec=Ticket)

        with patch.object(self.service, "get_ticket", return_value=expected_ticket) as get_ticket:
            result = self.service.get_ticket_from_branch("feature/ABC-123")

        get_ticket.assert_called_once_with("ABC", "123")
        self.assertIs(result, expected_ticket)

    def test_get_ticket_from_branch_failure(self):
        self.config.get_identifiers.return_value = ["ABC"]

        with self.assertRaises(TicketIdentifierNotFound):
            self.service.get_ticket_from_branch("feature/no-match")

    def test_prompt_ticket(self):
        conf = Mock()
        conf.url = "https://tickets.example.com"
        conf.description = "Main tickets"

        self.config.get_config.return_value = {"ABC": conf}
        self.prompter.ask.side_effect = ["ABC", "123"]

        expected_ticket = Mock(spec=Ticket)

        with patch.object(self.service, "get_ticket", return_value=expected_ticket) as get_ticket:
            result = self.service.prompt_ticket()

        self.config.get_config.assert_called_once_with()
        self.prompter.ask.assert_any_call("Prefix")
        self.prompter.ask.assert_any_call("Ticket number")
        get_ticket.assert_called_once_with("ABC", "123")
        self.assertEqual(result, expected_ticket)

    def test_prompt_ticket_reprompts_until_valid_prefix(self):
        conf = Mock()
        conf.url = "https://tickets.example.com"
        conf.description = "Main tickets"

        self.config.get_config.return_value = {"ABC": conf}
        self.prompter.ask.side_effect = ["BAD", "ABC", "123"]

        expected_ticket = Mock(spec=Ticket)

        with patch.object(self.service, "get_ticket", return_value=expected_ticket) as get_ticket:
            result = self.service.prompt_ticket()

        self.assertEqual(
            self.prompter.ask.call_args_list,
            [
                (("Prefix",),),
                (("Prefix",),),
                (("Ticket number",),),
            ],
        )
        get_ticket.assert_called_once_with("ABC", "123")
        self.assertEqual(result, expected_ticket)
