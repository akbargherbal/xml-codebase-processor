import pytest
from xml_directory_processor import should_include_file, should_ignore_path

class TestFileFiltering:
    """Test file inclusion/exclusion logic"""

    def test_should_include_file_size_limits(self):
        """Test file size filtering"""
        params = {"exclude_extensions": [], "json_size_threshold": 1024, "max_file_size": 10 * 1024}
        assert should_include_file("test.py", 5000, params) == True
        assert should_include_file("large.py", 20 * 1024, params) == False
        assert should_include_file("data.json", 2048, params) == False

    def test_should_ignore_path_patterns(self):
        """Test path ignore patterns"""
        ignore_patterns = ["node_modules", ".git", "*.pyc", "__pycache__"]
        assert should_ignore_path("project/node_modules/lib.js", ignore_patterns) == True
        assert should_ignore_path("src/__pycache__/module.pyc", ignore_patterns) == True
        assert should_ignore_path("src/main.py", ignore_patterns) == False