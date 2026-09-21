import unittest
from unittest.mock import MagicMock, patch

from sc.docker.docker import SCDocker


class TestSCDockerRunCommand(unittest.TestCase):
    def test_generate_docker_run_command_applies_configured_cpu_limit(self):
        sc_docker = SCDocker.__new__(SCDocker)
        sc_docker.config_manager = MagicMock()
        sc_docker.config_manager.max_cpus = 6
        sc_docker._stdout_connected_to_terminal = MagicMock(return_value=False)
        sc_docker._get_docker_group_id = MagicMock(return_value=None)

        with (
            patch("sc.docker.docker.STANDARD_MOUNT_DIRS", []),
            patch.dict(
                "os.environ",
                {"HOME": "/home/test-user", "USER": "test-user"},
                clear=True
            ),
        ):
            command = sc_docker._generate_docker_run_command(
                image="ghcr.io/example/image",
                tag="latest",
                container_name="example",
                image_name="image",
                x11=False,
                volumes=(),
                command=(),
            )

        self.assertIn("--cpus=6", command)
        self.assertFalse(any(arg.startswith("--cpuset-cpus") for arg in command))


if __name__ == "__main__":
    unittest.main()
