# Copyright 2025 RDK Management
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

import logging
from pathlib import Path
import requests

import yaml

logger = logging.getLogger(__name__)

class ProjectListDownloader:
    def __init__(self):
        self.supported_platforms = {
            "github": lambda token: {"Authorization": f"token {token}"},
            "gitlab": lambda token: {"PRIVATE-TOKEN": token},
        }

    def download(
            self,
            url: str,
            path: Path | str,
            platform: str | None = None,
            token: str | None = None
        ) -> Path:
        """Download a text file and write to a path.

        Can either use one of the classes supported platforms or no platform for
        publicly hosted files.
        """
        if platform and platform not in self.supported_platforms:
            raise ValueError(f"Unsupported platform: {platform}. Supported platforms are "
                             f"{', '.join(self.supported_platforms)}")

        header = self._get_auth_header(platform, token)
        try:
            response = requests.get(url, headers=header)
            response.raise_for_status()
            if not self._is_yaml_dict(response.text):
                raise RuntimeError("Downloaded text is not a valid yaml!")
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(response.text)
            return Path(path)
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch project list: {e}") from e

    def _get_auth_header(self, platform: str | None, token: str | None):
        if platform is not None:
            return self.supported_platforms[platform](token)

    def _is_yaml_dict(self, text: str):
        try:
            data = yaml.safe_load(text)
            return isinstance(data, dict)
        except yaml.YAMLError:
            return False