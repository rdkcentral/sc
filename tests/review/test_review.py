import unittest
from unittest.mock import MagicMock, patch

from sc.review.review import Review
from sc.review.exceptions import TicketIdentifierNotFound
from sc.review.models import CodeReview, RepoInfo


class TestReview(unittest.TestCase):

    def setUp(self):
        self.repo_source = MagicMock()
        self.ticket_service = MagicMock()
        self.git_service = MagicMock()
        self.prompter = MagicMock()

        self.review = Review(
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

        self.ticket = MagicMock(id=1, url="http://ticket")
        self.ticket_service.resolve.return_value = ("instance", self.ticket)

    @patch("builtins.print")
    def test_run_happy_path(self, mock_print):
        cr = CodeReview(status="OPEN", url="http://cr")
        self.git_service.get_git_review_data.return_value = cr
        self.ticket_service.match_branch.return_value = ("ABC", "123")
        self.prompter.yn.return_value = True

        self.review.run()

        self.ticket_service.update.assert_called_once()
        self.git_service.get_git_review_data.assert_called_once()
        self.ticket_service.resolve.assert_called_once_with("ABC", "123")

    @patch("builtins.print")
    def test_run_ticket_not_found_fallback(self, mock_print):
        self.ticket_service.match_branch.side_effect = TicketIdentifierNotFound("err")
        self.ticket_service.prompt_ticket.return_value = ("ABC", "123")
        self.git_service.get_git_review_data.return_value = CodeReview(status=None, url=None)
        self.prompter.yn.return_value = False

        self.review.run()

        self.ticket_service.prompt_ticket.assert_called_once()
        self.ticket_service.update.assert_not_called()

    @patch("builtins.print")
    def test_run_git_failure_creates_url(self, mock_print):
        self.ticket_service.match_branch.return_value = ("ABC", "123")
        self.git_service.get_git_review_data.return_value = None
        self.git_service.get_create_cr_url.return_value = "http://create"
        self.prompter.yn.return_value = False

        self.review.run()

        self.git_service.get_create_cr_url.assert_called_once()

    def test_create_comment_data(self):
        cr = CodeReview(status="OPEN", url="http://cr")
        ticket = MagicMock(url="http://ticket")

        result = self.review._create_comment_data(self.repo_info, ticket, cr, None)

        self.assertEqual(result.ticket_url, "http://ticket")
        self.assertEqual(result.review_status, "OPEN")
        self.assertEqual(result.review_url, "http://cr")

    def test_create_comment_data_no_cr(self):
        ticket = MagicMock(url="http://ticket")
        result = self.review._create_comment_data(self.repo_info, ticket, None, "http://create")

        self.assertEqual(result.ticket_url, "http://ticket")
        self.assertEqual(result.review_status, "Not Created")
        self.assertIsNone(result.review_url)
        self.assertEqual(result.create_cr_url, "http://create")

    def test_generate_combined_terminal_comment(self):
        c1 = MagicMock()
        c1.to_terminal.return_value = "A"
        c2 = MagicMock()
        c2.to_terminal.return_value = "B"

        result = self.review._generate_combined_terminal_comment([c1, c2])

        self.assertEqual(result, f"A\n{'-'*100}\nB")

    def test_generate_combined_ticket_comment(self):
        c1 = MagicMock()
        c1.to_ticket.return_value = "A"
        c2 = MagicMock()
        c2.to_ticket.return_value = "B"

        result = self.review._generate_combined_ticket_comment([c1, c2])

        self.assertEqual(result, f"A\n{'-'*100}\nB")


if __name__ == "__main__":
    unittest.main()