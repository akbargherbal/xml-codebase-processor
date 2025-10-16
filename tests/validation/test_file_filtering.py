# FILE: tests/validation/test_file_filtering.py

import pytest
from xml_directory_processor import should_include_file, should_ignore_path
import os


class TestFileFiltering:
    """Test file inclusion/exclusion logic"""

    def test_should_include_file_size_limits(self):
        """Test file size filtering"""
        params = {
            "exclude_extensions": [],
            "json_size_threshold": 1024,
            "max_file_size": 10 * 1024,
        }
        assert should_include_file("test.py", 5000, params) == True
        assert should_include_file("large.py", 20 * 1024, params) == False
        assert should_include_file("data.json", 2048, params) == False

    def test_should_ignore_path_patterns_simple_backward_compatibility(self):
        """Test original simple path ignore patterns for backward compatibility."""
        ignore_patterns = ["node_modules", ".git", "*.pyc", "__pycache__"]
        assert (
            should_ignore_path(
                os.path.join("project", "node_modules", "lib.js"), ignore_patterns
            )
            == True
        )
        assert (
            should_ignore_path(
                os.path.join("src", "__pycache__", "module.pyc"), ignore_patterns
            )
            == True
        )
        assert (
            should_ignore_path(os.path.join("src", "main.py"), ignore_patterns) == False
        )
        assert should_ignore_path(".git", ignore_patterns) == True

    def test_should_ignore_path_multi_segment(self):
        """Test that multi-segment path patterns are matched anywhere in the path."""
        ignore_patterns = ["integrity/firefox", "inject/dynamic-theme"]
        test_path_1 = os.path.join("project", "src", "integrity", "firefox", "file.js")
        test_path_2 = os.path.join("project", "inject", "dynamic-theme", "style.css")
        test_path_3 = os.path.join("project", "src", "main.py")

        assert should_ignore_path(test_path_1, ignore_patterns) == True
        assert should_ignore_path(test_path_2, ignore_patterns) == True
        assert should_ignore_path(test_path_3, ignore_patterns) == False

    def test_should_ignore_path_with_trailing_slash(self):
        """Test that patterns with trailing slashes correctly match directories."""
        ignore_patterns = ["node_modules/", "logs/"]
        test_path_1 = os.path.join("project", "node_modules", "lib.js")
        test_path_2 = os.path.join("logs", "app.log")
        assert should_ignore_path(test_path_1, ignore_patterns) == True
        assert should_ignore_path(test_path_2, ignore_patterns) == True

    def test_should_ignore_path_wildcard_in_multi_segment(self):
        """Test that multi-segment patterns with wildcards match correctly."""
        ignore_patterns = ["a/*/c", "x/y*z/w"]
        test_path_1 = os.path.join("a", "b", "c", "d.txt")
        test_path_2 = os.path.join("x", "y_and_z", "w", "file.js")
        test_path_3 = os.path.join("a", "b", "x", "d.txt")

        assert should_ignore_path(test_path_1, ignore_patterns) == True
        assert should_ignore_path(test_path_2, ignore_patterns) == True
        assert should_ignore_path(test_path_3, ignore_patterns) == False

    def test_should_ignore_path_windows_separators(self):
        """Test matching Unix-style patterns against Windows-style paths."""
        ignore_patterns = ["integrity/firefox"]
        windows_path = "C:\\Users\\Test\\project\\integrity\\firefox\\script.js"
        assert should_ignore_path(windows_path, ignore_patterns) == True
