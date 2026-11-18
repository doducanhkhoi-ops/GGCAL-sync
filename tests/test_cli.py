import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "main_sync.py"
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "sample_timetable.html"


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class TestCLI(unittest.TestCase):
    def test_help_flag(self):
        proc = run_cli("--help")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("--weeks", proc.stdout)
        self.assertIn("--dry-run", proc.stdout)
        self.assertIn("--parse-html", proc.stdout)

    def test_version_flag(self):
        proc = run_cli("--version")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("main_sync.py", proc.stdout)

    def test_parse_html_outputs_valid_json(self):
        proc = run_cli("--parse-html", str(FIXTURE_PATH))
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]["course"], "Kinh tế lượng")
        self.assertTrue(data[1]["is_makeup"])

    def test_invalid_weeks_exits_nonzero(self):
        proc = run_cli("--weeks", "0")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--weeks must be >= 1", proc.stdout)

    def test_missing_parse_html_file_exits_nonzero(self):
        proc = run_cli("--parse-html", "does_not_exist.html")
        self.assertEqual(proc.returncode, 1)


if __name__ == "__main__":
    unittest.main()
