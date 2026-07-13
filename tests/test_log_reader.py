import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


FLASK_APP_DIRECTORY = Path(__file__).resolve().parents[1] / "apps" / "flask"
sys.path.insert(0, str(FLASK_APP_DIRECTORY))

import log_reader


class LogReaderTests(unittest.TestCase):
    def test_missing_and_empty_directories_return_no_logs(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            self.assertEqual(log_reader.get_log_files(directory / "missing"), [])
            self.assertEqual(log_reader.get_log_files(directory), [])

    def test_reads_only_direct_log_files_in_name_order(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            (directory / "zeta.log").write_text("zeta\n", encoding="utf-8")
            (directory / "alpha.log").write_text("alpha\n", encoding="utf-8")
            (directory / "secret.env").write_text("SECRET=value\n", encoding="utf-8")
            (directory / "nested").mkdir()
            (directory / "nested" / "hidden.log").write_text("hidden\n", encoding="utf-8")

            logs = log_reader.get_log_files(directory)

            self.assertEqual([item["name"] for item in logs], ["alpha.log", "zeta.log"])
            self.assertNotIn("SECRET", "".join(item["content"] for item in logs))
            self.assertNotIn("hidden", "".join(item["content"] for item in logs))

    def test_large_log_keeps_only_the_last_500_lines(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            lines = [f"line {number}\n" for number in range(700)]
            (directory / "large.log").write_text("".join(lines), encoding="utf-8")

            result = log_reader.get_log_files(directory)[0]

            self.assertEqual(result["displayed_lines"], 500)
            self.assertEqual(result["total_lines"], 700)
            self.assertTrue(result["content"].startswith("line 200\n"))
            self.assertTrue(result["content"].endswith("line 699\n"))

    def test_invalid_utf8_is_replaced(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            (directory / "invalid.log").write_bytes(b"before\xffafter\n")

            result = log_reader.get_log_files(directory)[0]

            self.assertEqual(result["content"], "before\ufffdafter\n")

    def test_symlinks_are_skipped_to_prevent_path_traversal(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            outside = directory.parent / "outside.log"
            outside.write_text("must not be shown\n", encoding="utf-8")
            try:
                (directory / "linked.log").symlink_to(outside)
                self.assertEqual(log_reader.get_log_files(directory), [])
            finally:
                outside.unlink(missing_ok=True)

    def test_one_read_error_does_not_hide_other_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            broken = directory / "broken.log"
            healthy = directory / "healthy.log"
            broken.write_text("broken\n", encoding="utf-8")
            healthy.write_text("healthy\n", encoding="utf-8")
            original_reader = log_reader._read_log_tail

            def read_with_error(path, max_lines):
                if path.name == "broken.log":
                    raise PermissionError
                return original_reader(path, max_lines)

            with patch.object(log_reader, "_read_log_tail", side_effect=read_with_error):
                results = log_reader.get_log_files(directory)

            self.assertEqual(results[0]["error"], "Unable to read this log file.")
            self.assertEqual(results[1]["content"], "healthy\n")


if __name__ == "__main__":
    unittest.main()
