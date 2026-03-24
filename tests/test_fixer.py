import unittest
from unittest.mock import mock_open, patch

from docwatcher.fixer import apply_fix


class ApplyFixTests(unittest.TestCase):
    def test_replaces_matching_text(self):
        mocked_open = mock_open(read_data="Old text")

        with patch("builtins.open", mocked_open):
            success = apply_fix("README.md", "Old text", "New text")

        self.assertTrue(success)
        mocked_open().write.assert_called_with("New text")

    def test_appends_when_original_text_missing(self):
        mocked_open = mock_open(read_data="Existing text")

        with patch("builtins.open", mocked_open):
            success = apply_fix("README.md", "Missing text", "Generated text")

        self.assertTrue(success)
        mocked_open().write.assert_called_with("\n\nGenerated text\n")


if __name__ == "__main__":
    unittest.main()
