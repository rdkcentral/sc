import unittest
from unittest.mock import MagicMock, patch

from sc.docker.docker import SCDocker


class TestSCDockerRunCommand(unittest.TestCase):
    def test_generate_docker_run_command_applies_configured_cpu_limit(self):
        sc_docker = SCDocker.__new__(SCDocker)
        sc_docker.config_manager = MagicMock()
        sc_docker.config_manager.cpu_limit = 6
        sc_docker._stdout_connected_to_terminal = MagicMock(return_value=False)
        sc_docker._get_docker_group_id = MagicMock(return_value=None)

        with (
            patch("sc.docker.docker.STANDARD_MOUNT_DIRS", []),
            patch("sc.docker.docker.os.cpu_count", return_value=21),
            patch.dict(
                "os.environ",
                {"HOME": "/home/test-user", "USER": "test-user"},
                clear=True,
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

        self.assertIn("--cpuset-cpus=0-5", command)
        self.assertFalse(any(arg.startswith("--cpus=") for arg in command))

    def test_generate_docker_run_command_resolves_cpu_limits(self):
        sc_docker = SCDocker.__new__(SCDocker)
        sc_docker.config_manager = MagicMock()
        sc_docker._stdout_connected_to_terminal = MagicMock(return_value=False)
        sc_docker._get_docker_group_id = MagicMock(return_value=None)

        cases = (
            (24, 0, []),
            (24, -4, ["--cpuset-cpus=0-19"]),
            (24, -24, ["--cpuset-cpus=0-0"]),
            (24, -30, ["--cpuset-cpus=0-0"]),
            (24, 30, ["--cpuset-cpus=0-23"]),
            (24, 1, ["--cpuset-cpus=0-0"]),
            (20, -4, ["--cpuset-cpus=0-15"]),
            (19, -4, []),
            (None, -4, []),
        )
        for cpu_count, configured, expected in cases:
            with (
                self.subTest(cpu_count=cpu_count, cpu_limit=configured),
                patch("sc.docker.docker.STANDARD_MOUNT_DIRS", []),
                patch("sc.docker.docker.os.cpu_count", return_value=cpu_count),
            ):
                sc_docker.config_manager.cpu_limit = configured
                command = sc_docker._generate_docker_run_command(
                    image="ghcr.io/example/image",
                    tag="latest",
                    container_name="example",
                    image_name="image",
                    x11=False,
                    volumes=(),
                    command=(),
                )
                self.assertEqual(
                    [arg for arg in command if arg.startswith("--cpuset-cpus=")], expected
                )
                self.assertFalse(any(arg.startswith("--cpus=") for arg in command))

    def test_generate_docker_run_command_does_not_limit_nineteen_cpu_host(self):
        sc_docker = SCDocker.__new__(SCDocker)
        sc_docker.config_manager = MagicMock()
        sc_docker.config_manager.cpu_limit = 6
        sc_docker._stdout_connected_to_terminal = MagicMock(return_value=False)
        sc_docker._get_docker_group_id = MagicMock(return_value=None)

        with (
            patch("sc.docker.docker.STANDARD_MOUNT_DIRS", []),
            patch("sc.docker.docker.os.cpu_count", return_value=19),
            patch.dict(
                "os.environ",
                {"HOME": "/home/test-user", "USER": "test-user"},
                clear=True,
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

        self.assertFalse(any(arg.startswith("--cpus=") for arg in command))
        self.assertFalse(any(arg.startswith("--cpuset-cpus=") for arg in command))


if __name__ == "__main__":
    unittest.main()
