import unittest
from unittest.mock import MagicMock

from sc.review.ticket_service import TicketService
from sc.review.exceptions import TicketIdentifierNotFound

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

    def test_resolve(self):
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

        instance, ticket = self.service.resolve("jira", 123)

        self.factory.create.assert_called_once()
        instance.read_ticket.assert_called_once_with("ABC-123")
        self.assertEqual(instance, mock_instance)
        self.assertEqual(ticket, mock_ticket)

    def test_update(self):
        mock_instance = MagicMock()
        mock_ticket = MagicMock(id="ABC-123")

        self.service.update(mock_instance, mock_ticket, "comment")

        mock_instance.add_comment_to_ticket.assert_called_once_with("ABC-123", "comment")

    def test_match_branch_success(self):
        self.config.get_identifiers.return_value = ["ABC"]

        identifier, ticket_num = self.service.match_branch("feature/ABC-123")

        self.assertEqual(identifier, "ABC")
        self.assertEqual(ticket_num, "123")

    def test_match_branch_failure(self):
        self.config.get_identifiers.return_value = ["ABC"]

        with self.assertRaises(TicketIdentifierNotFound):
            self.service.match_branch("feature/no-match")

    def test_prompt_ticket(self):
        self.config.get_config.return_value = {"cfg": "value"}
        self.prompter.ticket_selection.return_value = ("ABC", "123")

        result = self.service.prompt_ticket()

        self.prompter.ticket_selection.assert_called_once_with({"cfg": "value"})
        self.assertEqual(result, ("ABC", "123"))
