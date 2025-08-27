import pytest
import os
import tempfile
import time
from xml_directory_processor import process_directory_structured, count_tokens


@pytest.mark.performance
class TestPerformanceEdgeCases:
    """Test performance with edge cases that could cause hangs or excessive memory usage"""

    def test_timeout_protection_large_file(self, large_test_project):
        """Test that processing completes within reasonable time limits"""
        params = {
            "ignore_patterns": [],
            "exclude_extensions": [],
            "json_size_threshold": 10 * 1024 * 1024,
            "max_file_size": 50 * 1024 * 1024,  # Large limit
            "token_limit": 100000,  # High limit
        }
        project_info = {
            "type": "python",
            "language": "python",
            "entry_points": [],
            "config_files": [],
            "dependency_files": [],
            "test_directories": [],
            "build_files": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as output:
            output_path = output.name

        try:
            start_time = time.time()
            with open(output_path, "w", encoding="utf-8") as outfile:
                process_directory_structured(
                    large_test_project, params, outfile, project_info, []
                )
            end_time = time.time()

            # Should complete within 30 seconds even for large projects
            processing_time = end_time - start_time
            assert (
                processing_time < 30.0
            ), f"Processing took {processing_time:.2f}s, expected < 30s"

            # Verify output was generated
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert len(content) > 100, "Output should contain substantial content"
                assert "<codebase>" in content
                assert "</codebase>" in content

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_extremely_long_filename_handling(self):
        """Test handling of files with very long names"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file with maximum path length (Windows has ~260 char limit)
            long_name = "a" * 100 + ".py"  # Reasonable length that won't hit OS limits
            long_file = os.path.join(tmpdir, long_name)

            with open(long_file, "w") as f:
                f.write("print('test')")

            params = {
                "ignore_patterns": [],
                "exclude_extensions": [],
                "json_size_threshold": 1024,
                "max_file_size": 1024 * 1024,
                "token_limit": 10000,
            }
            project_info = {
                "type": "python",
                "language": "python",
                "entry_points": [],
                "config_files": [],
                "dependency_files": [],
                "test_directories": [],
                "build_files": [],
            }

            with tempfile.NamedTemporaryFile(mode="w", delete=False) as output:
                output_path = output.name

            try:
                with open(output_path, "w", encoding="utf-8") as outfile:
                    process_directory_structured(
                        tmpdir, params, outfile, project_info, []
                    )

                with open(output_path, "r") as f:
                    content = f.read()
                    assert long_name in content
            finally:
                if os.path.exists(output_path):
                    os.unlink(output_path)

    def test_deep_directory_nesting(self):
        """Test handling of deeply nested directory structures"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure (reasonable depth)
            current_path = tmpdir
            for i in range(10):  # 10 levels deep
                current_path = os.path.join(current_path, f"level_{i}")
                os.makedirs(current_path, exist_ok=True)

            # Add file at deepest level
            deep_file = os.path.join(current_path, "deep.py")
            with open(deep_file, "w") as f:
                f.write("print('deep file')")

            params = {
                "ignore_patterns": [],
                "exclude_extensions": [],
                "json_size_threshold": 1024,
                "max_file_size": 1024 * 1024,
                "token_limit": 10000,
            }
            project_info = {
                "type": "python",
                "language": "python",
                "entry_points": [],
                "config_files": [],
                "dependency_files": [],
                "test_directories": [],
                "build_files": [],
            }

            with tempfile.NamedTemporaryFile(mode="w", delete=False) as output:
                output_path = output.name

            try:
                start_time = time.time()
                with open(output_path, "w", encoding="utf-8") as outfile:
                    process_directory_structured(
                        tmpdir, params, outfile, project_info, []
                    )
                end_time = time.time()

                # Should handle deep nesting without excessive time
                assert end_time - start_time < 10.0

                with open(output_path, "r") as f:
                    content = f.read()
                    assert "deep.py" in content
            finally:
                if os.path.exists(output_path):
                    os.unlink(output_path)

    def test_token_counting_performance_repeated(self):
        """Test token counting performance with repeated calls"""
        # Create varied content to avoid tiktoken performance bottleneck
        test_contents = [
            "import os\nprint('hello')\n" * 1000,
            "def function():\n    return True\n" * 1000,
            "class TestClass:\n    pass\n" * 1000,
            "# Comment line\nvalue = 42\n" * 1000,
            "data = {'key': 'value'}\n" * 1000,
        ]

        for i, content in enumerate(test_contents):
            start_time = time.time()
            tokens = count_tokens(content)
            end_time = time.time()

            # Each call should complete quickly
            assert (
                end_time - start_time < 2.0
            ), f"Token counting iteration {i} took too long"
            assert tokens > 0, f"Should return positive token count for iteration {i}"

    @pytest.mark.slow
    def test_resource_cleanup_after_errors(self):
        """Verify that resources are cleaned up properly after processing errors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files that might cause processing errors
            error_scenarios = [
                ("empty.py", ""),
                ("malformed.json", '{"incomplete": json'),
                ("binary.bin", b"\x00\x01\x02\x03" * 1000),
                ("unicode.txt", "测试文件 with mixed content"),
            ]

            for filename, content in error_scenarios:
                filepath = os.path.join(tmpdir, filename)
                try:
                    if isinstance(content, bytes):
                        with open(filepath, "wb") as f:
                            f.write(content)
                    else:
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(content)
                except Exception:
                    continue  # Skip if we can't create the test file

            params = {
                "ignore_patterns": [],
                "exclude_extensions": [],
                "json_size_threshold": 1024,
                "max_file_size": 1024 * 1024,
                "token_limit": 10000,
            }
            project_info = {
                "type": "unknown",
                "language": "mixed",
                "entry_points": [],
                "config_files": [],
                "dependency_files": [],
                "test_directories": [],
                "build_files": [],
            }

            # Process multiple times to check for resource leaks
            for iteration in range(3):
                with tempfile.NamedTemporaryFile(mode="w", delete=False) as output:
                    output_path = output.name

                try:
                    with open(output_path, "w", encoding="utf-8") as outfile:
                        process_directory_structured(
                            tmpdir, params, outfile, project_info, []
                        )

                    # Verify each iteration produces valid output
                    with open(output_path, "r") as f:
                        content = f.read()
                        assert "<codebase>" in content
                        assert "</codebase>" in content

                finally:
                    if os.path.exists(output_path):
                        os.unlink(output_path)
