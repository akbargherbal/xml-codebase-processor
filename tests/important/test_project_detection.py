import pytest
import os
import tempfile
from xml_directory_processor import detect_project_type

@pytest.mark.important
class TestProjectDetection:
    """Test project type detection accuracy - Important Priority"""

    @pytest.mark.parametrize(
        "project_type,files",
        [
            ("python", ["requirements.txt"]), ("python", ["setup.py"]),
            ("python", ["pyproject.toml"]), ("nodejs", ["package.json"]),
            ("rust", ["Cargo.toml"]), ("go", ["go.mod"]), ("java", ["pom.xml"]),
            ("java", ["build.gradle"]), ("php", ["composer.json"]), ("ruby", ["Gemfile"]),
        ]
    )
    def test_project_type_detection(self, project_type, files):
        """Test detection of various project types based on key files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            for filename in files:
                with open(os.path.join(tmpdir, filename), "w") as f:
                    f.write("# test content")
            project_info = detect_project_type(tmpdir)
            assert project_info["type"] == project_type

    def test_mixed_project_detection_priority(self):
        """Test handling of mixed-language projects"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "package.json"), "w") as f:
                f.write('{"name": "test"}')
            with open(os.path.join(tmpdir, "requirements.txt"), "w") as f:
                f.write("requests")
            project_info = detect_project_type(tmpdir)
            assert project_info["type"] in ["python", "nodejs"]

    def test_project_detection_in_subdirectories(self):
        """Test that project files in deep subdirectories are found"""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, "backend", "src")
            os.makedirs(subdir)
            with open(os.path.join(subdir, "setup.py"), "w") as f:
                f.write("from setuptools import setup\nsetup(name='test')")
            project_info = detect_project_type(tmpdir)
            assert project_info["type"] == "python"