# FILE PATH: tests/integration/test_include_exclude_integration.py
# LOCATION: tests/integration/test_include_exclude_integration.py
# DESCRIPTION: Integration tests for include/exclude functionality with real file system

"""
Integration tests for include/exclude functionality.
Tests end-to-end behavior with real file system operations.
"""

import pytest
import tempfile
import os
from pathlib import Path
import subprocess
import sys


@pytest.fixture
def test_project_structure(tmp_path):
    """
    Create a realistic project structure for testing.

    Structure:
    project/
    ├── src/
    │   ├── main.py
    │   ├── utils.py
    │   └── __pycache__/
    │       └── main.cpython-312.pyc
    ├── tests/
    │   ├── test_main.py
    │   └── test_utils.py
    ├── docs/
    │   ├── README.md
    │   └── guide.txt
    ├── build/
    │   └── output.so
    ├── .git/
    │   └── config
    └── README.md
    """
    project = tmp_path / "project"
    project.mkdir()

    # Source directory
    src = project / "src"
    src.mkdir()
    (src / "main.py").write_text("def main(): pass")
    (src / "utils.py").write_text("def helper(): pass")
    pycache = src / "__pycache__"
    pycache.mkdir()
    (pycache / "main.cpython-312.pyc").write_text("binary")

    # Tests directory
    tests = project / "tests"
    tests.mkdir()
    (tests / "test_main.py").write_text("def test_main(): pass")
    (tests / "test_utils.py").write_text("def test_helper(): pass")

    # Docs directory
    docs = project / "docs"
    docs.mkdir()
    (docs / "README.md").write_text("# Documentation")
    (docs / "guide.txt").write_text("Guide")

    # Build directory (should be ignored)
    build = project / "build"
    build.mkdir()
    (build / "output.so").write_text("binary")

    # Git directory (should be ignored)
    git = project / ".git"
    git.mkdir()
    (git / "config").write_text("git config")

    # Root README
    (project / "README.md").write_text("# Project")

    return project


def run_processor(project_path, output_path, *args):
    """Helper to run the xml_directory_processor with given arguments."""
    cmd = [
        sys.executable,
        "xml_directory_processor.py",
        str(project_path),
        "--output",
        str(output_path),
        *args,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def parse_output_files(output_path):
    """Parse the output file and extract processed file paths."""
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract file paths from <file path='...'> tags
    import re

    pattern = r"<file path='([^']+)'"
    matches = re.findall(pattern, content)
    return matches


class TestBasicInclude:
    """Test basic --include functionality."""

    def test_include_single_directory(self, test_project_structure, tmp_path):
        """Include only src directory."""
        output = tmp_path / "output.txt"
        result = run_processor(test_project_structure, output, "--include", "src")

        assert result.returncode == 0
        files = parse_output_files(output)

        # Should include src files
        assert any("src/main.py" in f for f in files)
        assert any("src/utils.py" in f for f in files)

        # Should NOT include other directories
        assert not any("tests/" in f for f in files)
        assert not any("docs/" in f for f in files)
        assert not any("README.md" == f for f in files)

    def test_include_multiple_directories(self, test_project_structure, tmp_path):
        """Include multiple directories."""
        output = tmp_path / "output.txt"
        result = run_processor(
            test_project_structure, output, "--include", "src", "tests"
        )

        assert result.returncode == 0
        files = parse_output_files(output)

        # Should include both src and tests
        assert any("src/main.py" in f for f in files)
        assert any("tests/test_main.py" in f for f in files)

        # Should NOT include docs
        assert not any("docs/" in f for f in files)

    def test_include_with_wildcards(self, test_project_structure, tmp_path):
        """Include files matching wildcard patterns."""
        output = tmp_path / "output.txt"
        result = run_processor(test_project_structure, output, "--include", "*.md")

        assert result.returncode == 0
        files = parse_output_files(output)

        # Should include all .md files
        assert any("README.md" in f for f in files)
        assert any("docs/README.md" in f for f in files)

        # Should NOT include .py or .txt files
        assert not any(".py" in f for f in files)
        assert not any(".txt" in f for f in files)

    def test_include_comma_separated(self, test_project_structure, tmp_path):
        """Test comma-separated include patterns."""
        output = tmp_path / "output.txt"
        result = run_processor(test_project_structure, output, "--include", "src,tests")

        assert result.returncode == 0
        files = parse_output_files(output)

        # Should include both
        assert any("src/" in f for f in files)
        assert any("tests/" in f for f in files)


class TestBasicExclude:
    """Test basic --exclude functionality."""

    def test_exclude_additional_directory(self, test_project_structure, tmp_path):
        """Exclude additional directory beyond defaults."""
        output = tmp_path / "output.txt"
        result = run_processor(test_project_structure, output, "--exclude", "docs")

        assert result.returncode == 0
        files = parse_output_files(output)

        # Should include src and tests (not excluded)
        assert any("src/" in f for f in files)
        assert any("tests/" in f for f in files)

        # Should NOT include docs (explicitly excluded)
        assert not any("docs/" in f for f in files)

        # Should NOT include default excludes (.git, __pycache__)
        assert not any(".git/" in f for f in files)
        assert not any("__pycache__" in f for f in files)

    def test_exclude_with_wildcards(self, test_project_structure, tmp_path):
        """Exclude files matching wildcard patterns."""
        output = tmp_path / "output.txt"
        result = run_processor(test_project_structure, output, "--exclude", "*.txt")

        assert result.returncode == 0
        files = parse_output_files(output)

        # Should NOT include .txt files
        assert not any("guide.txt" in f for f in files)

        # Should include other files
        assert any(".py" in f for f in files)
        assert any(".md" in f for f in files)

    def test_exclude_comma_separated(self, test_project_structure, tmp_path):
        """Test comma-separated exclude patterns."""
        output = tmp_path / "output.txt"
        result = run_processor(
            test_project_structure, output, "--exclude", "docs,build"
        )

        assert result.returncode == 0
        files = parse_output_files(output)

        assert not any("docs/" in f for f in files)
        assert not any("build/" in f for f in files)


class TestIncludeExcludeCombination:
    """Test combined include and exclude functionality."""

    def test_include_then_exclude(self, test_project_structure, tmp_path):
        """Include a directory but exclude subdirectories within it."""
        output = tmp_path / "output.txt"
        result = run_processor(
            test_project_structure,
            output,
            "--include",
            "src",
            "--exclude",
            "__pycache__",
        )

        assert result.returncode == 0
        files = parse_output_files(output)

        # Should include src Python files
        assert any("src/main.py" in f for f in files)
        assert any("src/utils.py" in f for f in files)

        # Should NOT include __pycache__ (excluded)
        assert not any("__pycache__" in f for f in files)

        # Should NOT include tests (not in include list)
        assert not any("tests/" in f for f in files)

    def test_include_multiple_exclude_specific(self, test_project_structure, tmp_path):
        """Include multiple directories but exclude specific files."""
        output = tmp_path / "output.txt"
        result = run_processor(
            test_project_structure,
            output,
            "--include",
            "src,tests",
            "--exclude",
            "*.pyc",
        )

        assert result.returncode == 0
        files = parse_output_files(output)

        # Should include .py files
        assert any("src/main.py" in f for f in files)
        assert any("tests/test_main.py" in f for f in files)

        # Should NOT include .pyc files
        assert not any(".pyc" in f for f in files)

    def test_exclude_overrides_include(self, test_project_structure, tmp_path):
        """Verify that exclude takes precedence over include."""
        # Create a file that matches both include and exclude
        (test_project_structure / "src" / "temp.py").write_text("# temp")

        output = tmp_path / "output.txt"
        result = run_processor(
            test_project_structure, output, "--include", "src", "--exclude", "temp.py"
        )

        assert result.returncode == 0
        files = parse_output_files(output)

        # Should include other src files
        assert any("src/main.py" in f for f in files)

        # Should NOT include temp.py (excluded despite being in src)
        assert not any("temp.py" in f for f in files)


class TestDefaultBehaviorPreservation:
    """Ensure default behavior is preserved when new flags aren't used."""

    def test_no_flags_processes_everything_except_defaults(
        self, test_project_structure, tmp_path
    ):
        """Without include/exclude, should process all except default ignores."""
        output = tmp_path / "output.txt"
        result = run_processor(test_project_structure, output)

        assert result.returncode == 0
        files = parse_output_files(output)

        # Should include normal files
        assert any("src/main.py" in f for f in files)
        assert any("tests/test_main.py" in f for f in files)
        assert any("README.md" in f for f in files)

        # Should NOT include default ignores
        assert not any(".git/" in f for f in files)
        assert not any("__pycache__" in f for f in files)

    def test_ignore_patterns_still_work(self, test_project_structure, tmp_path):
        """Original --ignore-patterns flag should still function."""
        output = tmp_path / "output.txt"
        result = run_processor(
            test_project_structure,
            output,
            "--ignore-patterns",
            ".git",
            "build",
            "tests",
        )

        assert result.returncode == 0
        files = parse_output_files(output)

        # Should include src
        assert any("src/" in f for f in files)

        # Should NOT include specified ignores
        assert not any(".git/" in f for f in files)
        assert not any("build/" in f for f in files)
        assert not any("tests/" in f for f in files)


class TestRealWorldUseCases:
    """Test realistic usage scenarios."""

    def test_analyze_only_source_code(self, test_project_structure, tmp_path):
        """Common case: analyze only src directory, exclude caches."""
        output = tmp_path / "output.txt"
        result = run_processor(
            test_project_structure,
            output,
            "--include",
            "src",
            "--exclude",
            "__pycache__",
            "*.pyc",
        )

        assert result.returncode == 0
        files = parse_output_files(output)

        # Should include only src Python files
        assert any("src/main.py" in f for f in files)
        assert any("src/utils.py" in f for f in files)
        assert len([f for f in files if "src/" in f and ".py" in f]) >= 2

        # Should exclude everything else
        assert not any("tests/" in f for f in files)
        assert not any("docs/" in f for f in files)
        assert not any("__pycache__" in f for f in files)

    def test_documentation_only_analysis(self, test_project_structure, tmp_path):
        """Process only documentation files."""
        output = tmp_path / "output.txt"
        result = run_processor(
            test_project_structure, output, "--include", "*.md", "docs"
        )

        assert result.returncode == 0
        files = parse_output_files(output)

        # Should include markdown and docs
        assert any("README.md" in f for f in files)
        assert any("docs/" in f for f in files)

        # Should NOT include code files
        assert not any(".py" in f for f in files)

    def test_exclude_generated_files(self, test_project_structure, tmp_path):
        """Exclude build artifacts and generated files."""
        # Create some generated files
        (test_project_structure / "generated.py").write_text("# auto-generated")
        (test_project_structure / "src" / "generated.py").write_text("# auto-generated")

        output = tmp_path / "output.txt"
        result = run_processor(
            test_project_structure, output, "--exclude", "build", "generated.py"
        )

        assert result.returncode == 0
        files = parse_output_files(output)

        # Should NOT include generated files
        assert not any("generated.py" in f for f in files)
        assert not any("build/" in f for f in files)


class TestEdgeCasesIntegration:
    """Test edge cases in real scenarios."""

    def test_empty_include_list(self, test_project_structure, tmp_path):
        """Empty include list should process everything (except excludes)."""
        output = tmp_path / "output.txt"
        result = run_processor(
            test_project_structure, output, "--include"  # Empty include
        )

        # Should work without error
        assert result.returncode == 0

    def test_nonexistent_include_pattern(self, test_project_structure, tmp_path):
        """Including non-existent directory should result in empty output."""
        output = tmp_path / "output.txt"
        result = run_processor(
            test_project_structure, output, "--include", "nonexistent"
        )

        assert result.returncode == 0
        files = parse_output_files(output)

        # Should not include any files
        assert len(files) == 0

    def test_overlapping_include_exclude(self, test_project_structure, tmp_path):
        """Test when same pattern appears in both include and exclude."""
        output = tmp_path / "output.txt"
        result = run_processor(
            test_project_structure, output, "--include", "src", "--exclude", "src"
        )

        assert result.returncode == 0
        files = parse_output_files(output)

        # Exclude should win
        assert not any("src/" in f for f in files)

    def test_nested_directory_filtering(self, test_project_structure, tmp_path):
        """Test filtering in nested directory structures."""
        # Create deeper nesting
        nested = test_project_structure / "src" / "models" / "user"
        nested.mkdir(parents=True)
        (nested / "model.py").write_text("class User: pass")

        output = tmp_path / "output.txt"
        result = run_processor(
            test_project_structure, output, "--include", "src/models"
        )

        assert result.returncode == 0
        files = parse_output_files(output)

        # Should include nested files
        assert any("src/models/user/model.py" in f for f in files)


class TestPerformanceIntegration:
    """Test performance with realistic project sizes."""

    def test_large_directory_with_include(self, tmp_path):
        """Test performance when including specific directories in large projects."""
        import time

        # Create a larger project structure
        project = tmp_path / "large_project"
        project.mkdir()

        # Create multiple directories with files
        for dir_name in ["src", "tests", "docs", "scripts", "data"]:
            dir_path = project / dir_name
            dir_path.mkdir()
            for i in range(50):  # 50 files per directory
                (dir_path / f"file_{i}.py").write_text(f"# File {i}")

        output = tmp_path / "output.txt"

        start = time.time()
        result = run_processor(project, output, "--include", "src", "--exclude", "data")
        duration = time.time() - start

        assert result.returncode == 0
        files = parse_output_files(output)

        # Should only process src files (50 files)
        src_files = [f for f in files if "src/" in f]
        assert len(src_files) == 50

        # Should complete in reasonable time
        assert duration < 10.0  # Should be much faster than 10 seconds


class TestErrorHandling:
    """Test error handling in integration scenarios."""

    def test_invalid_pattern_syntax(self, test_project_structure, tmp_path):
        """Test handling of invalid pattern syntax."""
        output = tmp_path / "output.txt"
        # Some regex special chars might cause issues
        result = run_processor(
            test_project_structure, output, "--include", "[[[invalid"
        )

        # Should not crash
        assert result.returncode in [0, 1]  # Either success or graceful failure

    def test_permission_denied_directory(self, test_project_structure, tmp_path):
        """Test handling when directory has permission issues."""
        # This test is platform-specific and may not work on all systems
        if os.name != "posix":
            pytest.skip("Permission test only on POSIX systems")

        restricted = test_project_structure / "restricted"
        restricted.mkdir()
        (restricted / "secret.py").write_text("secret")
        os.chmod(restricted, 0o000)

        output = tmp_path / "output.txt"
        result = run_processor(test_project_structure, output)

        # Should handle gracefully
        assert result.returncode == 0

        # Cleanup
        os.chmod(restricted, 0o755)


class TestCommandLineInterface:
    """Test CLI argument parsing and validation."""

    def test_help_shows_new_options(self):
        """Verify --include and --exclude appear in help."""
        result = subprocess.run(
            [sys.executable, "xml_directory_processor.py", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "--include" in result.stdout
        assert "--exclude" in result.stdout

    def test_multiple_include_patterns_syntax(self, test_project_structure, tmp_path):
        """Test various ways to specify multiple patterns."""
        output = tmp_path / "output.txt"

        # Space-separated
        result1 = run_processor(
            test_project_structure, output, "--include", "src", "tests"
        )
        assert result1.returncode == 0

        # Comma-separated
        result2 = run_processor(
            test_project_structure, tmp_path / "output2.txt", "--include", "src,tests"
        )
        assert result2.returncode == 0

        # Both should produce similar results
        files1 = parse_output_files(output)
        files2 = parse_output_files(tmp_path / "output2.txt")
        assert set(files1) == set(files2)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
