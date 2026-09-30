import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class ComposeSetupTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.link = self.home / ".docker/cli-plugins/docker-compose"
        script = Path(__file__).with_name("install.sh").read_text()
        self.block = script.split('COMPOSE_LINK=', 1)[1].split('# mise', 1)[0]
        self.block = 'COMPOSE_LINK=' + self.block

    def run_setup(self):
        subprocess.run(["bash", "-ec", self.block],
                       env={**os.environ, "HOME": str(self.home)}, check=True)

    def test_new_machine_and_repeat(self):
        self.run_setup()
        self.run_setup()
        prefix = subprocess.check_output(["brew", "--prefix"], text=True).strip()
        self.assertEqual(os.readlink(self.link),
                         prefix + "/lib/docker/cli-plugins/docker-compose")
        self.assertFalse((self.home / ".docker/config.json").exists())

    def test_preserve_existing_file(self):
        self.link.parent.mkdir(parents=True)
        self.link.write_text("existing")
        self.run_setup()
        self.assertEqual(self.link.read_text(), "existing")

    def test_preserve_existing_symlink(self):
        self.link.parent.mkdir(parents=True)
        self.link.symlink_to(self.home / "other-plugin")
        self.run_setup()
        self.assertEqual(os.readlink(self.link), str(self.home / "other-plugin"))


if __name__ == "__main__":
    unittest.main()
