import unittest

from sc.review.ticket_service import TicketService
from sc.review.exceptions import TicketIdentifierNotFound


class FakeTicketInstance:
    def __init__(self):
        self.read_called_with = None
        self.update_called_with = None

    def read_ticket(self, ticket_id):
        self.read_called_with = ticket_id
        return {"id": ticket_id}

    def add_comment_to_ticket(self, ticket_id, comment):
        self.update_called_with = (ticket_id, comment)


class FakeFactory:
    def __init__(self):
        self.kwargs = None
        self.instance = FakeTicketInstance()

    def create(self, **kwargs):
        self.kwargs = kwargs
        return self.instance


class FakeConfig:
    def __init__(self, prefix="ABC-", identifiers=None):
        self.prefix = prefix
        self.identifiers = identifiers or ["ABC", "XYZ"]

    def get_ticket_host_data(self, identifier):
        return type("Cfg", (), {
            "provider": "p",
            "url": "url",
            "api_key": "key",
            "auth_type": "auth",
            "username": "user",
            "cert": "cert",
            "project_prefix": self.prefix
        })()

    def get_ticket_host_identifiers(self):
        return self.identifiers


class TestTicketService(unittest.TestCase):

    def test_resolve_builds_ticket_id_with_prefix(self):
        config = FakeConfig(prefix="ABC-")
        factory = FakeFactory()
        service = TicketService(config, factory)

        instance, ticket = service.resolve("ABC", "123")

        self.assertEqual(ticket["id"], "ABC-123")
        self.assertEqual(instance.read_called_with, "ABC-123")

    def test_resolve_builds_ticket_id_without_prefix(self):
        config = FakeConfig(prefix=None)
        factory = FakeFactory()
        service = TicketService(config, factory)

        instance, ticket = service.resolve("ABC", "123")

        self.assertEqual(ticket["id"], "123")
        self.assertEqual(instance.read_called_with, "123")

    def test_resolve_passes_correct_args_to_factory(self):
        config = FakeConfig()
        factory = FakeFactory()
        service = TicketService(config, factory)

        service.resolve("ABC", "123")

        self.assertEqual(factory.kwargs["provider"], "p")
        self.assertEqual(factory.kwargs["url"], "url")
        self.assertEqual(factory.kwargs["token"], "key")
        self.assertEqual(factory.kwargs["auth_type"], "auth")
        self.assertEqual(factory.kwargs["username"], "user")
        self.assertEqual(factory.kwargs["cert"], "cert")

    # ---- update ----

    def test_update_calls_instance(self):
        service = TicketService(None, None)
        instance = FakeTicketInstance()

        service.update(instance, "ABC-1", "comment")

        self.assertEqual(instance.update_called_with, ("ABC-1", "comment"))

    # ---- match_branch ----

    def test_match_branch_with_dash(self):
        config = FakeConfig(identifiers=["ABC"])
        service = TicketService(config, None)

        identifier, num = service.match_branch("feature/ABC-123-test")

        self.assertEqual(identifier, "ABC")
        self.assertEqual(num, "123")

    def test_match_branch_with_underscore(self):
        config = FakeConfig(identifiers=["ABC"])
        service = TicketService(config, None)

        identifier, num = service.match_branch("bugfix/ABC_456")

        self.assertEqual(identifier, "ABC")
        self.assertEqual(num, "456")

    def test_match_branch_multiple_identifiers(self):
        config = FakeConfig(identifiers=["XYZ", "ABC"])
        service = TicketService(config, None)

        identifier, num = service.match_branch("feature/ABC-999")

        self.assertEqual(identifier, "ABC")
        self.assertEqual(num, "999")

    def test_match_branch_raises_when_no_match(self):
        config = FakeConfig(identifiers=["ABC"])
        service = TicketService(config, None)

        with self.assertRaises(TicketIdentifierNotFound):
            service.match_branch("feature/no-match")

