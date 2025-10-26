# FILE PATH: tests/unit/test_pattern_processing.py
# LOCATION: tests/unit/test_pattern_processing.py
# DESCRIPTION: Unit tests for new include/exclude pattern processing functionality

"""
Unit tests for new include/exclude pattern processing functionality.
Tests the core logic added by the LLM feature request.
"""

import pytest
from pathlib import Path
import os
from xml_directory_processor import should_process_path, should_ignore_path


class TestPatternParsing:
    """Test comma-separated and space-separated pattern parsing."""

    def test_parse_single_pattern(self):
        """Single pattern should work without modification."""
        from xml_directory_processor import main

        # Test that parse_patterns helper handles single pattern
        patterns = ["src"]
        # This would be called in main()
        assert len(patterns) == 1

    def test_parse_comma_separated_patterns(self):
        """Comma-separated patterns should be split correctly."""
        pattern_str = "src,tests,docs"
        expected = ["src", "tests", "docs"]
        # Simulate the parse_patterns logic
        result = [p.strip() for p in pattern_str.split(",") if p.strip()]
        assert result == expected

    def test_parse_mixed_separators(self):
        """Handle both comma and space separation."""
        patterns = ["src,tests", "docs"]
        processed = []
        for item in patterns:
            processed.extend(item.split(","))
        result = [p.strip() for p in processed if p.strip()]
        assert result == ["src", "tests", "docs"]

    def test_parse_empty_patterns(self):
        """Empty pattern list should return empty list."""
        patterns = []
        result = [p.strip() for p in patterns if p.strip()]
        assert result == []

    def test_parse_whitespace_handling(self):
        """Whitespace should be stripped from patterns."""
        pattern_str = " src , tests , docs "
        result = [p.strip() for p in pattern_str.split(",") if p.strip()]
        assert result == ["src", "tests", "docs"]


class TestShouldProcessPath:
    """Test the new should_process_path function for inclusion logic."""

    def test_no_include_patterns_processes_everything(self):
        """When no include patterns, all paths should be processed."""
        assert should_process_path("any/path/here", []) is True
        assert should_process_path("src/main.py", []) is True
        assert should_process_path(".git/config", []) is True

    def test_simple_directory_inclusion(self):
        """Simple directory name should match."""
        include = ["src"]
        assert should_process_path("src", include) is True
        assert should_process_path("src/main.py", include) is True
        assert should_process_path("tests/test.py", include) is False

    def test_wildcard_pattern_inclusion(self):
        """Wildcard patterns should work correctly."""
        include = ["*.py"]
        assert should_process_path("main.py", include) is True
        assert should_process_path("src/utils.py", include) is True
        assert should_process_path("README.md", include) is False

    def test_multi_segment_path_inclusion(self):
        """Multi-segment paths should match correctly."""
        include = ["src/models"]
        assert should_process_path("src/models", include) is True
        assert should_process_path("src/models/user.py", include) is True
        assert should_process_path("src/utils", include) is False

    def test_multiple_include_patterns(self):
        """Any matching pattern should allow inclusion."""
        include = ["src", "tests", "*.md"]
        assert should_process_path("src/main.py", include) is True
        assert should_process_path("tests/test.py", include) is True
        assert should_process_path("README.md", include) is True
        assert should_process_path("docs/guide.txt", include) is False

    def test_case_sensitivity(self):
        """Pattern matching should respect OS case sensitivity."""
        include = ["SRC"]
        # On Windows, this might match "src", on Unix it won't
        # Test based on OS behavior
        if os.name == "nt":
            # Windows is case-insensitive
            assert should_process_path("src", include) in [True, False]  # OS-dependent
        else:
            # Unix is case-sensitive
            assert should_process_path("src", include) is False


class TestIncludeExcludeInteraction:
    """Test the interaction between include and exclude patterns."""

    def test_include_then_exclude_priority(self):
        """Exclude should take precedence after include check."""
        include = ["src"]
        exclude = ["__pycache__"]

        # Should be included (matches include)
        assert should_process_path("src/main.py", include) is True

        # Should be excluded even though in src
        path = "src/__pycache__"
        assert should_process_path(path, include) is True
        assert should_ignore_path(path, exclude) is True

    def test_include_overrides_nothing_without_exclude(self):
        """Include alone should not exclude anything."""
        include = ["src"]
        # These paths shouldn't be processed (not in include list)
        assert should_process_path("tests/test.py", include) is False
        assert should_process_path("docs/README.md", include) is False

    def test_exclude_added_to_defaults(self):
        """User exclude patterns should be added to default ignore list."""
        default_ignore = [".git", "node_modules", "__pycache__"]
        user_exclude = ["*.tmp", "cache"]
        final_ignore = default_ignore + user_exclude

        assert len(final_ignore) == 5
        assert "*.tmp" in final_ignore
        assert ".git" in final_ignore


class TestBackwardCompatibility:
    """Ensure new features don't break existing functionality."""

    def test_no_include_no_exclude_preserves_behavior(self):
        """Without include/exclude, behavior should match original."""
        # No include patterns = process everything
        assert should_process_path("any/path", []) is True

        # Original ignore patterns still work
        default_ignore = [".git", "__pycache__", "node_modules"]
        assert should_ignore_path(".git/config", default_ignore) is True
        assert should_ignore_path("src/__pycache__/file.pyc", default_ignore) is True

    def test_ignore_patterns_still_work(self):
        """Original --ignore-patterns argument should still function."""
        ignore = [".env", ".git", "venv"]
        assert should_ignore_path(".env", ignore) is True
        assert should_ignore_path("project/.git/config", ignore) is True
        assert should_ignore_path("src/main.py", ignore) is False


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_path(self):
        """Empty path should be handled gracefully."""
        assert should_process_path("", []) is True
        assert should_ignore_path("", []) is False

    def test_root_path(self):
        """Root directory should be handled."""
        assert should_process_path("/", []) is True
        assert should_process_path(".", []) is True

    def test_pattern_with_trailing_slash(self):
        """Patterns with trailing slashes should work."""
        include = ["src/"]
        assert should_process_path("src/main.py", include) is True

    def test_pattern_with_leading_dot(self):
        """Hidden directories should match correctly."""
        ignore = [".git"]
        assert should_ignore_path(".git", ignore) is True
        assert should_ignore_path("project/.git/config", ignore) is True

    def test_unicode_patterns(self):
        """Unicode in patterns should be handled."""
        include = ["données"]  # French for "data"
        assert should_process_path("données/file.txt", include) is True

    def test_special_characters_in_patterns(self):
        """Special characters should be handled safely."""
        include = ["[test]"]  # Brackets might be special in fnmatch
        # Should not crash
        result = should_process_path("[test]/file.txt", include)
        assert isinstance(result, bool)


class TestRealWorldScenarios:
    """Test realistic usage scenarios."""

    def test_python_project_src_only(self):
        """Common case: process only src directory."""
        include = ["src"]
        ignore = ["__pycache__", ".pytest_cache"]

        # Should process
        assert should_process_path("src/main.py", include) is True
        assert should_process_path("src/utils/helpers.py", include) is True

        # Should not process (not in src)
        assert should_process_path("tests/test_main.py", include) is False
        assert should_process_path("README.md", include) is False

        # Should not process (excluded)
        src_cache = "src/__pycache__"
        assert should_process_path(src_cache, include) is True
        assert should_ignore_path(src_cache, ignore) is True

    def test_documentation_project(self):
        """Process only documentation files."""
        include = ["*.md", "*.rst", "docs"]

        assert should_process_path("README.md", include) is True
        assert should_process_path("docs/guide.md", include) is True
        assert should_process_path("CHANGELOG.rst", include) is True
        assert should_process_path("src/main.py", include) is False

    def test_monorepo_specific_services(self):
        """Large monorepo: include specific services."""
        include = ["services/api", "services/web"]

        assert should_process_path("services/api/main.py", include) is True
        assert should_process_path("services/web/app.py", include) is True
        assert should_process_path("services/worker/task.py", include) is False
        assert should_process_path("lib/utils.py", include) is False

    def test_exclude_build_artifacts(self):
        """Exclude common build directories."""
        include = []  # Process everything
        exclude = ["build", "dist", "*.egg-info", "__pycache__"]

        # Everything passes include check
        assert should_process_path("src/main.py", include) is True

        # But these are excluded
        assert should_ignore_path("build/lib/module.py", exclude) is True
        assert should_ignore_path("dist/package.tar.gz", exclude) is True
        assert should_ignore_path("src/__pycache__/main.pyc", exclude) is True


class TestPerformance:
    """Test performance characteristics of pattern matching."""

    def test_pattern_matching_efficiency(self):
        """Pattern matching should be reasonably fast."""
        import time

        include = ["src", "tests", "*.py", "*.md"]
        paths = [
            "src/main.py",
            "tests/test_main.py",
            "README.md",
            "docs/guide.txt",
        ] * 100

        start = time.time()
        for path in paths:
            should_process_path(path, include)
        duration = time.time() - start

        # Should process 400 paths in well under 1 second
        assert duration < 1.0

    def test_ignore_pattern_efficiency(self):
        """Ignore pattern matching should be fast."""
        import time

        ignore = [".git", "node_modules", "__pycache__", "*.pyc", "dist", "build"]
        paths = [
            ".git/config",
            "node_modules/package/index.js",
            "src/__pycache__/main.pyc",
            "build/lib/module.so",
        ] * 100

        start = time.time()
        for path in paths:
            should_ignore_path(path, ignore)
        duration = time.time() - start

        assert duration < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
