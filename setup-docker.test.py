import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class DockerSetupTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.config = self.home / ".docker/config.json"
        self.config.parent.mkdir(parents=True)
        self.repo = self.root / "dotfiles"
        (self.repo / "docker").mkdir(parents=True)
        self.prefix = self.root / "brew prefix"
        self.plugin = self.prefix / "lib/docker/cli-plugins/docker-compose"
        self.plugin.parent.mkdir(parents=True)
        self.plugin.write_text("plugin")

    def run_setup(self):
        return subprocess.run(
            ["bash", str(Path(__file__).with_name("setup-docker.sh")),
             str(self.repo), str(self.prefix)],
            env={**os.environ, "HOME": str(self.home)},
            capture_output=True, text=True,
        )

    def test_new_machine_and_repeat(self):
        for _ in range(2):
            self.assertEqual(self.run_setup().returncode, 0)
        link = self.home / ".docker/cli-plugins/docker-compose"
        self.assertEqual(link.resolve(), self.plugin.resolve())
        self.assertFalse(self.config.exists())

    def test_preserve_local_config(self):
        self.config.write_text('{"auths":{"example":{}}}')
        self.assertEqual(self.run_setup().returncode, 0)
        self.assertEqual(self.config.read_text(), '{"auths":{"example":{}}}')

    def test_migrate_managed_config(self):
        source = self.repo / "docker/config.json"
        source.write_text('{"auths":{"example":{}}}')
        self.config.symlink_to(source)
        self.assertEqual(self.run_setup().returncode, 0)
        self.assertFalse(self.config.is_symlink())
        self.assertEqual(self.config.read_bytes(), source.read_bytes())
        self.assertEqual(self.config.stat().st_mode & 0o777, 0o600)

    def test_remove_broken_managed_link(self):
        self.config.symlink_to(self.repo / "docker/config.json")
        self.assertEqual(self.run_setup().returncode, 0)
        self.assertFalse(self.config.is_symlink())

    def test_preserve_existing_plugin(self):
        link = self.home / ".docker/cli-plugins/docker-compose"
        link.parent.mkdir(parents=True)
        link.write_text("existing plugin")
        self.assertEqual(self.run_setup().returncode, 0)
        self.assertEqual(link.read_text(), "existing plugin")

    def test_missing_plugin_fails(self):
        self.plugin.unlink()
        self.assertNotEqual(self.run_setup().returncode, 0)


if __name__ == "__main__":
    unittest.main()
