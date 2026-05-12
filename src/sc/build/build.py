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
import sys

from repo_library import RepoLibrary
from yaml_runner import YamlRunner

logger = logging.getLogger(__name__)

def build(args: tuple[str, ...], config: str | None = None):
    if not config:
        try:
            config = _find_config()
        except FileNotFoundError as e:
            logger.error(e)
            sys.exit(1)

    yr = YamlRunner(str(config), program="SC Build")
    yr.run(args)

def _find_config() -> Path:
    repo_root = RepoLibrary.get_repo_root_dir(Path.cwd())
    if not repo_root:
        raise FileNotFoundError("Not in a Repo workspace!")
    config_file = repo_root / 'manifests' / 'config.yaml'
    if not config_file.exists():
        raise FileNotFoundError("No 'config.yaml' found in Repo manifests dir!")
    return config_file
    