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

import shlex

class DockerRunBuilder:
    """
    Helper for constructing `docker run` command invocations.

    This builder assembles the arguments for a `docker run` command,
    including container name, hostname, volume mounts, environment
    variables, and interactive flags, and composes a bash command
    sequence to be executed inside the container.
    """
    def __init__(
            self,
            image: str,
            tag: str = "latest"
        ):
        self.image = image
        self.tag = tag
        self.docker_args = [
            'docker',
            'run',
            '--rm',
            '--net=host'
        ]
        self.bash_commands = [
            "source /usr/local/bin/bashext.sh"
        ]

    def add_bash_command(self, bash_command: str):
        """Add a bash command to be run inside the docker."""
        self.bash_commands.append(bash_command)

    def add_name(self, name: str):
        """Set the container name."""
        self.docker_args += ['--name', name]

    def add_hostname(self, hostname: str):
        """Set the container hostname."""
        self.docker_args += ['--hostname', hostname]

    def add_volume_mount(self, volume: str):
        """Mount a volume into the container (-v)."""
        self.docker_args += ['-v', volume]

    def add_env_var(self, var_name: str, value: str | None = None):
        """Add an environment variable, optionally with a value."""
        if value is not None:
            self.docker_args += ['-e', f"{var_name}={value}"]
        else:
            self.docker_args += ['-e', f"{var_name}"]

    def add_interactive_flag(self):
        """Enable interactive TTY (-it)."""
        self.docker_args += ['-it']

    def build(self) -> list[str]:
        """Build the final docker run argument list."""
        return [
            *self.docker_args,
            f"{self.image}:{self.tag}",
            shlex.join(["bash", "-c", " && ".join(self.bash_commands)])
        ]
