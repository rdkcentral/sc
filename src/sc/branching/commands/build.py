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
"""Run build commands using commands predefined in a config."""

from dataclasses import dataclass
import logging
from pathlib import Path
import sys

from .command import Command

from yaml_runner import YamlRunner
from yaml_runner.exceptions import YamlRunnerError

logger = logging.getLogger(__name__)

@dataclass
class Build(Command):
    config: str | None
    arguments: tuple[str, ...]

    def run_git_command(self):
        if self.config:
            config_path = self._resolve_input_path(self.config)
        else:
            config_path = self._search_config_path_in_dir(self.top_dir)

        logger.info(f"Using config file: {config_path}")
        self._execute_yaml_runner(config_path)

    def run_repo_command(self):
        if self.config:
            config_path = self._resolve_input_path(self.config)
        else:
            config_path = self._search_config_path_in_dir(self.top_dir / ".repo" / "manifests")

        logger.info(f"Using config file: {config_path}")
        self._execute_yaml_runner(config_path)

    def _resolve_input_path(self, path: str | Path) -> Path:
        path = Path(path).expanduser().resolve()

        if not path.exists():
            logger.error(f"User inputted path {path} doesn't exist")
            sys.exit(1)

        return path

    def _search_config_path_in_dir(self, search_dir: Path) -> Path:
        path = search_dir / "config.yaml"

        if not path.exists():
            logger.error(f"No config.yaml found in {search_dir}")
            sys.exit(1)

        return path

    def _execute_yaml_runner(self, config_path: Path):
        try:
            yr = YamlRunner(config=str(config_path), program="sc build", fail_fast=True)
        except YamlRunnerError as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)

        try:
            completed_commands = yr.execute(list(self.arguments))
            exit_code = max((c.exit_code for c in completed_commands), default=0)
            sys.exit(exit_code)
        except YamlRunnerError as e:
            logger.error(f"Failed to execute command: {e}")
            sys.exit(1)
