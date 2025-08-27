import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from xml_directory_processor import detect_project_type, process_directory_structured


@pytest.mark.integration
class TestIntegration:
    """Integration tests with realistic project structures"""

    def test_typical_python_project_processing(self):
        """Test processing a typical Python project structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            structure = {
                "setup.py": "from setuptools import setup\nsetup(name='test')",
                "requirements.txt": "requests==2.25.1",
                "src/main.py": "import requests\n\ndef main():\n    print('Hello')",
                "src/utils.py": "def helper():\n    return True",
                "tests/test_main.py": "import pytest\n\ndef test_main():\n    assert True",
                "README.md": "# Test Project",
                ".gitignore": "*.pyc\n__pycache__/",
            }
            for path, content in structure.items():
                full_path = os.path.join(tmpdir, path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w") as f:
                    f.write(content)

            project_info = detect_project_type(tmpdir)
            assert project_info["type"] == "python"

            params = {
                "ignore_patterns": [".git", "__pycache__", "*.pyc"],
                "exclude_extensions": [".pyc"],
                "json_size_threshold": 1024,
                "max_file_size": 1024 * 1024,
                "token_limit": 10000,
            }
            output_path = os.path.join(tmpdir, "output.xml")
            with open(output_path, "w", encoding="utf-8") as outfile:
                process_directory_structured(tmpdir, params, outfile, project_info, [])

            with open(output_path, "r") as f:
                content = f.read()
                assert "type='python'" in content
                assert "main.py" in content
                assert "test_main.py" in content

                # FIXED: Account for the change from <file> to <dep> in dependencies section
                # Count actual file entries vs dependency entries separately
                file_tags = content.count("<file ")
                file_close_tags = content.count("</file>")
                dep_tags = content.count("<dep>")
                dep_close_tags = content.count("</dep>")

                # Verify XML balance for both file and dependency sections
                assert (
                    file_tags == file_close_tags
                ), f"Unbalanced file tags: {file_tags} opening vs {file_close_tags} closing"
                assert (
                    dep_tags == dep_close_tags
                ), f"Unbalanced dependency tags: {dep_tags} opening vs {dep_close_tags} closing"

                # Basic structure validation
                assert "<codebase>" in content
                assert "</codebase>" in content
                assert "<files>" in content
                assert "</files>" in content

    def test_notebook_conversion_integration(self):
        """Test notebook conversion with mocked nbconvert"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock notebook file
            notebook_file = os.path.join(tmpdir, "analysis.ipynb")
            notebook_content = {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": ["import pandas as pd\ndf = pd.read_csv('data.csv')"],
                    }
                ],
                "metadata": {"kernelspec": {"name": "python3"}},
            }

            with open(notebook_file, "w") as f:
                import json

                json.dump(notebook_content, f)

            # Mock nbconvert
            mock_markdown_content = "# Analysis Notebook\n\n```python\nimport pandas as pd\ndf = pd.read_csv('data.csv')\n```"

            with patch("xml_directory_processor.nbconvert") as mock_nbconvert:
                mock_exporter = MagicMock()
                mock_exporter.from_filename.return_value = (mock_markdown_content, {})
                mock_nbconvert.MarkdownExporter.return_value
