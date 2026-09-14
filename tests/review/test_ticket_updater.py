#!/usr/bin/env python3
import unittest
from unittest.mock import Mock, MagicMock, patch

from sc.review.ticket_updater import TicketUpdater
from sc.services.tickets.exceptions import TicketIdentifierNotFound
from sc.services.tickets.ticket import Ticket
from sc.exceptions import ScError
from sc.review.models import CodeReview, CRStatus, RepoInfo

class TestTicketUpdater(unittest.TestCase):

    def setUp(self):
        self.repo_source = MagicMock()
        self.ticket_service = MagicMock()
        self.git_service = MagicMock()
        self.prompter = MagicMock()

        self.ticket_updater = TicketUpdater(
            repo_source=self.repo_source,
            ticket_service=self.ticket_service,
            git_service=self.git_service,
            prompter=self.prompter
        )

        self.repo_info = RepoInfo(
            branch="feature/test",
            directory="dir",
            remote_url="url",
            commit_sha="sha",
            commit_author="author",
            commit_date="date",
            commit_message="msg"
        )

        self.repo_source.get_repos.return_value = [self.repo_info]
        self.repo_source.active_branch = "feature/test"

        self.ticket = MagicMock(id=1, url="http://ticket", title="Ticket title")
        self.ticket.to_terminal.return_value = "ticket terminal output"

        self.ticket_service.resolve.return_value = ("instance", self.ticket)

    @patch("builtins.print")
    def test_run_happy_path(self, mock_print):
        cr = CodeReview(status="OPEN", url="http://cr", create_url=None)
        self.git_service.get_code_review_data.return_value = cr
        ticket = Mock(spec=Ticket)
        self.ticket_service.get_ticket_from_branch.return_value = ticket

        # Use this ticket? yes. Update ticket? yes.
        self.prompter.yn.return_value = True
        self.prompter.choice.return_value = "y"

        self.ticket_updater.run()

        self.ticket_service.get_ticket_from_branch.assert_called_once_with("feature/test")
        self.git_service.get_code_review_data.assert_called_once_with(self.repo_info)
        ticket.add_comment.assert_called_once()

    @patch("builtins.print")
    def test_run_ticket_not_found_fallback(self, mock_print):
        self.ticket_service.get_ticket_from_branch.side_effect = TicketIdentifierNotFound("err")
        ticket = Mock(spec=Ticket)
        self.ticket_service.prompt_ticket.return_value = ticket
        self.git_service.get_git_review_data.return_value = CodeReview(status=None, url=None, create_url="donut")

        # Use this ticket? yes. Update ticket? no.
        self.prompter.yn.return_value = True
        self.prompter.choice.return_value = "n"

        self.ticket_updater.run()

        self.ticket_service.prompt_ticket.assert_called_once()
        ticket.add_comment.assert_not_called()

    @patch("builtins.print")
    def test_ticket_unable_to_resolve_fallback(self, mock_print):
        self.ticket_service.get_ticket_from_branch.side_effect = ScError("cannot resolve")
        ticket = Mock(spec=Ticket)
        self.ticket_service.prompt_ticket.return_value = ticket

        self.prompter.yn.return_value = True

        result = self.ticket_updater._get_ticket()

        self.ticket_service.get_ticket_from_branch.assert_called_once()
        self.ticket_service.prompt_ticket.assert_called_once()
        self.assertEqual(result, ticket)

    @patch("builtins.print")
    def test_user_rejects_detected_ticket_and_enters_new_ticket(self, mock_print):
        detected_ticket = Mock(spec=Ticket)
        self.ticket_service.get_ticket_from_branch.return_value = detected_ticket
        manual_ticket = Mock(spec=Ticket)
        self.ticket_service.prompt_ticket.return_value = manual_ticket

        # Use detected ticket? no. Use manual ticket? yes.
        self.prompter.yn.side_effect = [False, True]

        ticket = self.ticket_updater._get_ticket()

        self.assertEqual(ticket, manual_ticket)
        self.ticket_service.get_ticket_from_branch.assert_called_once()
        self.ticket_service.prompt_ticket.assert_called_once()

    def test_create_comment_data(self):
        cr = CodeReview(status="OPEN", url="http://cr")
        ticket = MagicMock(url="http://ticket", title="Ticket title")

        result = self.ticket_updater._create_comment_data(self.repo_info, ticket, cr)

        self.assertEqual(result.ticket_url, "http://ticket")
        self.assertEqual(result.ticket_title, "Ticket title")
        self.assertEqual(result.code_review.status, "OPEN")
        self.assertEqual(result.code_review.url, "http://cr")

    def test_create_comment_data_no_cr(self):
        ticket = MagicMock(url="http://ticket", title="Ticket title")
        cr = CodeReview(url=None, status=CRStatus.NOT_CREATED, create_url="http://create")

        result = self.ticket_updater._create_comment_data(
            self.repo_info,
            ticket,
            cr
        )

        self.assertEqual(result.ticket_url, "http://ticket")
        self.assertEqual(result.ticket_title, "Ticket title")
        self.assertEqual(result.code_review.status, "Not Created")
        self.assertIsNone(result.code_review.url)
        self.assertEqual(result.code_review.create_url, "http://create")

    def test_generate_combined_terminal_comment(self):
        c1 = MagicMock()
        c1.to_terminal.return_value = "A"

        c2 = MagicMock()
        c2.to_terminal.return_value = "B"

        result = self.ticket_updater._generate_combined_terminal_comment([c1, c2])

        self.assertEqual(result, f"A\n{'-'*100}\nB")

    def test_generate_combined_ticket_comment(self):
        c1 = MagicMock()
        c1.to_ticket.return_value = "A"

        c2 = MagicMock()
        c2.to_ticket.return_value = "B"

        result = self.ticket_updater._generate_combined_ticket_comment([c1, c2])

        self.assertEqual(result, f"A\n{'-'*100}\nB")

    def test_refresh_code_reviews(self):
        ticket = Mock(spec=Ticket)
        self.ticket_service.get_ticket_from_branch.return_value = ticket

        first_cr = CodeReview(
            status=CRStatus.NOT_CREATED,
            url=None,
            create_url="http://create"
        )
        refreshed_cr = CodeReview(
            status="OPEN",
            url="http://cr",
            create_url=None
        )

        self.git_service.get_code_review_data.side_effect = [
            first_cr,
            refreshed_cr,
        ]

        # Accept ticket, then refresh, then don't update ticket.
        self.prompter.yn.return_value = True
        self.prompter.choice.side_effect = ["r", "n"]

        self.ticket_updater.run()

        self.assertEqual(self.git_service.get_code_review_data.call_count, 2)
        self.git_service.get_code_review_data.assert_any_call(self.repo_info)
        ticket.add_comment.assert_not_called()

        self.assertEqual(
            self.prompter.choice.call_args_list[0].args,
            (
                "Update ticket? [y/n/r - refresh code reviews]",
                ("y", "n", "r"),
            ),
        )
        self.assertEqual(
            self.prompter.choice.call_args_list[1].args,
            (
                "Update ticket? [y/n]",
                ("y", "n"),
            ),
        )

if __name__ == "__main__":
    unittest.main()