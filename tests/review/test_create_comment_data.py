from datetime import datetime
import unittest

from sc.review.review import CommentData, Review
from sc.review.models import CodeReview, CRStatus, RepoInfo

class TestCreateCommentData(unittest.TestCase):
    def setUp(self):
        self.review = Review("/tmp")
        self.repo_info = RepoInfo(
            branch="feature-123",
            directory="/tmp",
            remote_url="https://github.com/org/repo.git",
            commit_sha="1234567890",
            commit_author="Jane Doe <jane@example.com>",
            commit_date=datetime(2024, 1, 1),
            commit_message="Test commit message"
        )

        # avoid gitflow logic interfering
        self.review._get_target_branch = lambda *_: "develop"

    def test_with_review(self):
        cr = CodeReview("http://review-url", CRStatus.OPEN)

        data = self.review._create_comment_data(self.repo_info, "http://pr-url", cr)

        self.assertIsInstance(data, CommentData)
        self.assertEqual(data.review_status, "Open")
        self.assertEqual(data.review_url, "http://review-url")

    def test_without_review(self):
        data = self.review._create_comment_data(self.repo_info, "http://pr-url", None)

        self.assertEqual(data.review_status, "Not Created")
        self.assertIsNone(data.review_url)

    def test_commit_fields_are_populated(self):
        data = self.review._create_comment_data(self.repo_info, "http://pr-url", None)

        self.assertEqual(data.commit_sha, "1234567890")
        self.assertEqual(data.commit_author, "Jane Doe <jane@example.com>")
        self.assertEqual(data.commit_message, "Test commit message")
        self.assertEqual(data.commit_date, datetime(2024, 1, 1))

    def test_create_pr_url_is_used(self):
        data = self.review._create_comment_data(self.repo_info, "http://expected-url", None)

        self.assertIn("http://expected-url", data.create_pr_url)
