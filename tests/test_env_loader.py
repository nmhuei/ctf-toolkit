"""Tests for zero-dependency .env loader (ctf_downloader.utils.env_loader)."""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from ctf_downloader.utils.env_loader import parse_dotenv_text, load_dotenv


class TestEnvLoader(unittest.TestCase):
    def test_parse_dotenv_text(self):
        sample = """
        # Comment line
        CTF_THEME=matrix
        export CTF_DEBUG="1"
        CTF_SOLVER_MAX_WORKERS = '5' # inline comment
        EMPTY_VAR=
        QUOTED_HASH="foo # not comment"
        SINGLE_QUOTED='bar # also not'
        """
        parsed = parse_dotenv_text(sample)
        self.assertEqual(parsed["CTF_THEME"], "matrix")
        self.assertEqual(parsed["CTF_DEBUG"], "1")
        self.assertEqual(parsed["CTF_SOLVER_MAX_WORKERS"], "5")
        self.assertEqual(parsed["EMPTY_VAR"], "")
        self.assertEqual(parsed["QUOTED_HASH"], "foo # not comment")
        self.assertEqual(parsed["SINGLE_QUOTED"], "bar # also not")

    def test_load_dotenv_does_not_override_by_default(self):
        with tempfile.TemporaryDirectory() as td:
            env_file = Path(td) / ".env"
            env_file.write_text("TEST_KEY_CTF=from_file\n", encoding="utf-8")

            # Preset in os.environ
            os.environ["TEST_KEY_CTF"] = "from_env"
            try:
                loaded = load_dotenv(env_file, override=False)
                self.assertEqual(os.environ["TEST_KEY_CTF"], "from_env")
                self.assertIn("TEST_KEY_CTF", loaded)
            finally:
                os.environ.pop("TEST_KEY_CTF", None)

    def test_load_dotenv_populates_missing_keys(self):
        with tempfile.TemporaryDirectory() as td:
            env_file = Path(td) / ".env"
            env_file.write_text("UNIQUE_CTF_KEY_123=magic_value\n", encoding="utf-8")

            self.assertNotIn("UNIQUE_CTF_KEY_123", os.environ)
            try:
                loaded = load_dotenv(env_file)
                self.assertEqual(os.environ.get("UNIQUE_CTF_KEY_123"), "magic_value")
                self.assertEqual(loaded.get("UNIQUE_CTF_KEY_123"), "magic_value")
            finally:
                os.environ.pop("UNIQUE_CTF_KEY_123", None)

    def test_load_dotenv_with_override(self):
        with tempfile.TemporaryDirectory() as td:
            env_file = Path(td) / ".env"
            env_file.write_text("OVERRIDE_TEST_KEY=from_file\n", encoding="utf-8")

            os.environ["OVERRIDE_TEST_KEY"] = "from_env"
            try:
                load_dotenv(env_file, override=True)
                self.assertEqual(os.environ["OVERRIDE_TEST_KEY"], "from_file")
            finally:
                os.environ.pop("OVERRIDE_TEST_KEY", None)


if __name__ == "__main__":
    unittest.main()
