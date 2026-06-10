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

"""Defensive guards on Artifactory registry API methods (issue #64)."""

import unittest

from sc.docker.registry_apis.artifactory import ArtifactoryAPI


class TestArtifactoryFetchImages(unittest.TestCase):

    def setUp(self):
        self.api = ArtifactoryAPI()

    def test_missing_namespace_raises_value_error(self):
        # The "not enough values to unpack" crash from #64 — now a clean
        # ValueError with a hint that points at the fix.
        with self.assertRaises(ValueError) as cm:
            self.api.fetch_images(
                "example.artifactory.com", "user", "token")
        self.assertIn("namespace", str(cm.exception).lower())

    def test_empty_registry_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.api.fetch_images("", "user", "token")


class TestArtifactoryFetchTags(unittest.TestCase):

    def setUp(self):
        self.api = ArtifactoryAPI()

    def test_missing_namespace_raises_value_error(self):
        with self.assertRaises(ValueError) as cm:
            self.api.fetch_tags(
                "example.artifactory.com", "user", "token", "some-image")
        self.assertIn("namespace", str(cm.exception).lower())


if __name__ == "__main__":
    unittest.main()
