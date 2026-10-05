import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from sc.go_cli import cli


class GoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sc go ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        manifests = self.root / ".repo" / "manifests"
        manifests.mkdir(parents=True)
        (self.root / ".repo" / "manifest.xml").write_text(
            '<manifest><include name="default.xml"/></manifest>'
        )
        (manifests / "default.xml").write_text('''<manifest>
            <remote name="origin" fetch="https://example.test"/>
            <default remote="origin" revision="main"/>
            <project name="team/alpha" path="apps/alpha">
                <annotation name="GIT_LOCK_STATUS" value="READ_ONLY"/>
            </project>
            <project name="team/alpha-tools" path="tools/alpha-tools"/>
            <project name="space" path="apps/space dir"/>
            <project name="missing"/>
            <include name="extra.xml"/>
            <remove-project name="removed"/>
        </manifest>''')
        (manifests / "extra.xml").write_text('''<manifest>
            <project name="included"/>
            <project name="removed"/>
        </manifest>''')
        for relative in ("apps/alpha", "tools/alpha-tools", "apps/space dir", "included"):
            (self.root / relative).mkdir(parents=True)
        self.runner = CliRunner()
        self.cwd = patch("sc.go_cli.Path.cwd", return_value=self.root / "apps" / "alpha")
        self.cwd.start()
        self.addCleanup(self.cwd.stop)

    def test_destinations(self):
        for query, relative in (("root", "."), ("manifest", ".repo/manifests"),
                                ("ALPHA", "apps/alpha"), ("team/alpha", "apps/alpha"),
                                ("apps/alpha", "apps/alpha"), ("space", "apps/space dir"),
                                ("included", "included"), ("tools$", "tools/alpha-tools")):
            with self.subTest(query=query):
                result = self.runner.invoke(cli, ["go", query])
                self.assertEqual(result.exit_code, 0, result.output)
                self.assertEqual(result.stdout, str(self.root / relative) + "\n")

    def test_failures_have_no_destination(self):
        for query, message in (("team", "Multiple projects"), ("removed", "No project"),
                               ("missing", "Directory does not exist"), ("[", "Invalid value")):
            with self.subTest(query=query):
                result = self.runner.invoke(cli, ["go", query])
                self.assertNotEqual(result.exit_code, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn(message, result.stderr)

    def test_listing_and_verbose_keep_stdout_clean(self):
        result = self.runner.invoke(cli, ["go", "-l"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(result.stdout, "")
        self.assertIn("READ_ONLY", result.stderr)
        result = self.runner.invoke(cli, ["go", "--v", "alpha"])
        self.assertEqual(result.stdout, str(self.root / "apps/alpha") + "\n")
        self.assertIn("REPO_REMOTE: [ origin ]", result.stderr)
        self.assertIn("REPO_RREV: [ main ]", result.stderr)
        result = self.runner.invoke(cli, ["go", "--w", "lpha"])
        self.assertNotEqual(result.exit_code, 0)

    def test_invalid_workspace_and_manifest(self):
        with patch("sc.go_cli.Path.cwd", return_value=self.root.parent):
            result = self.runner.invoke(cli, ["go", "root"])
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("does not belong", result.stderr)
        (self.root / ".repo/manifest.xml").write_text("<broken")
        result = self.runner.invoke(cli, ["go", "alpha"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Cannot read workspace manifest", result.stderr)

    def test_bash_integration(self):
        self.check_shell_integration("bash")

    @unittest.skipUnless(shutil.which("zsh"), "Zsh is not installed")
    def test_zsh_integration(self):
        self.check_shell_integration("zsh")

    def test_go_init_shell_selection(self):
        default = self.runner.invoke(cli, ["go-init"])
        bash = self.runner.invoke(cli, ["go-init", "bash"])
        zsh = self.runner.invoke(cli, ["go-init", "zsh"])
        for result in (default, bash, zsh):
            self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(default.stdout, bash.stdout)
        self.assertIn("emulate -L zsh;", zsh.stdout)
        invalid = self.runner.invoke(cli, ["go-init", "fish"])
        self.assertEqual(invalid.exit_code, 2)
        self.assertEqual(invalid.stdout, "")

    def check_shell_integration(self, shell):
        # Exercise the real entry point and shell function, including an old alias.
        environment = dict(os.environ)
        environment["PATH"] = str(Path(sys.executable).parent) + os.pathsep + environment["PATH"]
        environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
        setup = "shopt -s expand_aliases\n" if shell == "bash" else ""
        script = setup + '''
alias go='false'
eval "$(sc go-init "$1")"
go space || exit 10
printf '%s\n' "$PWD"
go absent 2>/dev/null && exit 11
printf '%s\n' "$PWD"
go --help >/dev/null || exit 12
go -l 2>/dev/null || exit 13
printf '%s\n' "$PWD"
go root || exit 14
printf '%s\n' "$PWD"
'''
        flags = ["--noprofile", "--norc"] if shell == "bash" else ["-f"]
        result = subprocess.run([shell, *flags, "-c", script, "go-test", shell],
                                cwd=self.root, env=environment, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(),
                         [str(self.root / "apps/space dir")] * 3 + [str(self.root)])
