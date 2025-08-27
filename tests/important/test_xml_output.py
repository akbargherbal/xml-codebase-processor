import pytest
import os
import tempfile
import xml.etree.ElementTree as ET
from xml_directory_processor import process_directory_structured


@pytest.mark.important
class TestXMLOutputIntegrity:
    """Test XML output format and special character handling - Important Priority"""

    def test_xml_special_characters_in_content(self):
        """Test that special XML characters in file content do not break the output"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = os.path.join(tmpdir, "src")
            os.makedirs(test_dir)
            malicious_content = (
                "Here is some code with <tag> & \"ampersand\" and 'quotes'."
            )
            with open(os.path.join(test_dir, "test.txt"), "w") as f:
                f.write(malicious_content)

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

            output_path = os.path.join(tmpdir, "output.xml")
            with open(output_path, "w", encoding="utf-8") as outfile:
                process_directory_structured(tmpdir, params, outfile, project_info, [])

            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert "<codebase>" in content
                assert "</codebase>" in content
                assert "<file path=" in content
                assert malicious_content in content

    def test_xml_structure_with_unicode_filenames(self):
        """Test XML output with unicode characters in filenames"""
        with tempfile.TemporaryDirectory() as tmpdir:
            unicode_file = os.path.join(tmpdir, "测试_αβγ.py")
            with open(unicode_file, "w", encoding="utf-8") as f:
                f.write("print('unicode test')")

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

            output_path = os.path.join(tmpdir, "output.xml")
            with open(output_path, "w", encoding="utf-8") as outfile:
                process_directory_structured(tmpdir, params, outfile, project_info, [])

            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert "测试_αβγ.py" in content
                assert "<codebase>" in content and "</codebase>" in content

    def test_xml_well_formedness_parsing(self):
        """Test that output can be parsed as valid XML structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            with open(os.path.join(tmpdir, "test.py"), "w") as f:
                f.write("print('hello')")

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

            output_path = os.path.join(tmpdir, "output.xml")
            with open(output_path, "w", encoding="utf-8") as outfile:
                process_directory_structured(tmpdir, params, outfile, project_info, [])

            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Remove content blocks for XML parsing (they contain code, not XML)
            xml_content = content
            import re

            xml_content = re.sub(r"```.*?```", "", xml_content, flags=re.DOTALL)

            try:
                root = ET.fromstring(xml_content)
                assert root.tag == "codebase"

                # Check for specific structure elements
                project = root.find("project")
                assert project is not None
                assert project.get("type") == "python"

                files_section = root.find("files")
                assert files_section is not None

                file_elements = files_section.findall("file")
                assert len(file_elements) >= 1

                # Check for error attributes in files (should be None for normal files)
                for file_elem in file_elements:
                    if file_elem.get("error"):
                        pytest.fail(
                            f"File has error attribute: {file_elem.get('path')}"
                        )

            except ET.ParseError as e:
                pytest.fail(f"XML parsing failed: {str(e)}")
