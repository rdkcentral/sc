# Copyright 2026 RDK Management
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

"""Tests for registry URL validation in sc.docker.docker (issue #64)."""

import unittest
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from sc.docker.docker import SCDocker


def _make_sc_docker(whitelist=None):
    """Build a SCDocker with the bits we don't exercise stubbed out."""
    sc = SCDocker.__new__(SCDocker)
    sc.whitelisted_registries = whitelist
    return sc


class TestValidateRegistryOnLogin(unittest.TestCase):
    """_validate_registry_on_login rejects malformed registry URLs (#64)."""

    def setUp(self):
        self.sc = _make_sc_docker()

    # ---- valid ---------------------------------------------------------

    def test_ghcr_org_url_is_accepted(self):
        # Should not exit.
        self.sc._validate_registry_on_login("ghcr.io/myorg")

    def test_artifactory_namespace_url_is_accepted(self):
        self.sc._validate_registry_on_login("example.artifactory.com/docker-registry")

    def test_artifactory_nested_namespace_is_accepted(self):
        self.sc._validate_registry_on_login(
            "example.artifactory.com/docker-registry/sub/path")

    def test_host_with_port_is_accepted(self):
        self.sc._validate_registry_on_login("localhost:5000/myrepo")

    def test_hyphenated_labels_are_accepted(self):
        self.sc._validate_registry_on_login("my-registry.example.com/my-repo")

    # ---- invalid -------------------------------------------------------

    def test_host_without_namespace_exits(self):
        # Reproduces the original "not enough values to unpack" failure mode.
        with self.assertRaises(SystemExit):
            self.sc._validate_registry_on_login("example.artifactory.com")

    def test_prompt_prefix_pasted_into_input_exits(self):
        # The exact paste accident from the bug report.
        with self.assertRaises(SystemExit):
            self.sc._validate_registry_on_login(
                "> : example.artifactory.com/docker-registry")

    def test_leading_whitespace_exits(self):
        with self.assertRaises(SystemExit):
            self.sc._validate_registry_on_login(
                "  example.artifactory.com/docker-registry")

    def test_trailing_whitespace_exits(self):
        with self.assertRaises(SystemExit):
            self.sc._validate_registry_on_login(
                "example.artifactory.com/docker-registry  ")

    def test_protocol_in_url_exits(self):
        # `host` shouldn't be a URL — strip scheme.
        with self.assertRaises(SystemExit):
            self.sc._validate_registry_on_login("https://ghcr.io/myorg")

    def test_empty_string_exits(self):
        with self.assertRaises(SystemExit):
            self.sc._validate_registry_on_login("")

    def test_just_a_slash_exits(self):
        with self.assertRaises(SystemExit):
            self.sc._validate_registry_on_login("/")

    def test_localhost_registry_is_accepted(self):
        # `localhost/myrepo` is a perfectly valid local-registry URL.
        # Docker spec is permissive about the host part.
        self.sc._validate_registry_on_login("localhost/myrepo")

    # ---- whitelist interplay ------------------------------------------

    def test_whitelist_rejection_runs_after_format_check(self):
        sc = _make_sc_docker(whitelist=["ghcr.io/allowed"])
        with self.assertRaises(SystemExit):
            sc._validate_registry_on_login("ghcr.io/not-allowed")

    def test_whitelist_allowed_url_is_accepted(self):
        sc = _make_sc_docker(whitelist=["ghcr.io/allowed"])
        sc._validate_registry_on_login("ghcr.io/allowed")


class TestPromptRegistryUrlStripsInput(unittest.TestCase):
    """_prompt_registry_url strips whitespace before validating (#64)."""

    def test_input_with_surrounding_whitespace_is_stripped_then_accepted(self):
        import click
        sc = _make_sc_docker()

        captured = {}

        @click.command()
        def fake_cmd():
            captured["result"] = sc._prompt_registry_url()

        result = CliRunner().invoke(
            fake_cmd, input="  ghcr.io/myorg  \n", catch_exceptions=False)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(captured["result"], "ghcr.io/myorg")

    def test_input_with_prompt_prefix_is_rejected_with_clear_error(self):
        import click
        sc = _make_sc_docker()

        @click.command()
        def fake_cmd():
            sc._prompt_registry_url()

        # Click's prompt() retries on each empty line; supply one line then
        # nothing else so the eventual SystemExit from the validator surfaces.
        result = CliRunner().invoke(
            fake_cmd,
            input="> : ghcr.io/myorg\n",
            catch_exceptions=False)
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("invalid registry URL", result.output)


if __name__ == "__main__":
    unittest.main()
