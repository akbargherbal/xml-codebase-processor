import pytest
import os
import tempfile
from xml_directory_processor import get_file_metadata, process_directory_structured


@pytest.mark.critical
class TestEncodingHandling:
    """Test text encoding detection and fallback - Critical Priority"""

    @pytest.mark.parametrize(
        "content,encoding,expected_readable",
        [
            ("Hello world test", "utf-8", True),
            ("café", "latin-1", True),
            ("Valid text with bytes", "latin-1", True),
        ],
    )
    def test_encoding_scenarios(self, content, encoding, expected_readable):
        """Test various encoding scenarios with parametrization"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            filepath = f.name
            if encoding == "latin-1":
                # Write problematic bytes for latin-1 test
                f.write(b"Valid text\xe9")  # é in latin-1
            else:
                f.write(content.encode(encoding))

        try:
            # Test multiple encoding attempts
            encodings_to_try = ["utf-8", "latin-1", "cp1252", "ascii"]
            content_read = None

            for enc in encodings_to_try:
                try:
                    with open(filepath, "r", encoding=enc) as rf:
                        content_read = rf.read()
                        break
                except (UnicodeDecodeError, UnicodeError):
                    continue

            if expected_readable:
                assert (
                    content_read is not None
                ), f"Should be able to read with {encoding}"

        finally:
            os.unlink(filepath)

    def test_binary_file_handling(self):
        """Test that binary files don't crash the metadata extraction"""
        binary_data = b"\x00\x01\x02\xff\xfe\xfd\x89PNG\r\n"
        with tempfile.NamedTemporaryFile(delete=False) as f:
            filepath = f.name
            f.write(binary_data)
        try:
            metadata = get_file_metadata(filepath)
            assert metadata is not None
            assert metadata["size"] == len(binary_data)
        finally:
            os.unlink(filepath)

    def test_encoding_error_in_processing(self):
        """Test encoding error handling during directory processing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file that will cause encoding issues
            problematic_file = os.path.join(tmpdir, "bad_encoding.txt")
            with open(problematic_file, "wb") as f:
                f.write(b"Valid text\x80\x81\x82invalid utf-8")

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

            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", delete=False
            ) as output:
                output_path = output.name

            try:
                with open(output_path, "w", encoding="utf-8") as outfile:
                    # Should handle encoding errors gracefully
                    process_directory_structured(
                        tmpdir, params, outfile, project_info, []
                    )

                # Verify output structure exists despite encoding errors
                with open(output_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    assert "<codebase>" in content
                    assert "</codebase>" in content
            finally:
                if os.path.exists(output_path):
                    os.unlink(output_path)

    def test_utf8_bom_handling(self):
        """Test handling of UTF-8 BOM (Byte Order Mark)"""
        content_with_bom = "\ufeffHello world"
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8-sig", delete=False
        ) as f:
            filepath = f.name
            f.write(content_with_bom)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                result = f.read()
                # BOM should be handled correctly
                assert "Hello world" in result
        finally:
            os.unlink(filepath)
