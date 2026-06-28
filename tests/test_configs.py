import json
import unittest
from unittest.mock import mock_open, patch

import configs.python


class TestConfigs(unittest.TestCase):
    def setUp(self):
        # Reload the module to ensure it's in a clean state if needed,
        # but since we are testing the function itself, we can just access it.
        self.load_json = configs.python._load_json

    @patch("pathlib.Path.exists")
    def test_load_json_file_not_found(self, mock_exists):
        mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError) as cm:
            self.load_json("non_existent.json")
        self.assertIn("Config file not found", str(cm.exception))

    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="invalid json")
    def test_load_json_invalid_json(self, mock_file, mock_exists):
        mock_exists.return_value = True
        with self.assertRaises(json.JSONDecodeError):
            self.load_json("invalid.json")

    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    def test_load_json_success(self, mock_file, mock_exists):
        mock_exists.return_value = True
        result = self.load_json("valid.json")
        self.assertEqual(result, {"key": "value"})


if __name__ == "__main__":
    unittest.main()
