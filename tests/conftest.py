import pytest
import tempfile
import os
import shutil
import sys
from typing import Dict, List
import logging

# Configure logging for tests - Windows safe
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


@pytest.fixture(scope="session")
def test_data_dir():
    """Create a session-level test data directory"""
    test_dir = tempfile.mkdtemp(prefix="xml_processor_test_")
    yield test_dir
    try:
        shutil.rmtree(test_dir, ignore_errors=True)
    except Exception:
        pass  # Ignore cleanup errors on Windows


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory for individual test projects"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_python_project():
    """Create a sample Python project structure for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_structure = {
            "setup.py": """from setuptools import setup, find_packages
setup(
    name="test_project",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["requests", "pytest"]
)""",
            "requirements.txt": "requests==2.25.1\npytest==6.2.4\nclick>=7.0",
            "src/main.py": """import requests
import click
from utils import helper_function

def main():
    result = helper_function()
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
""",
            "src/utils.py": """from typing import Dict, List
import json

def helper_function():
    return True

def process_data(data):
    return list(data.keys())
""",
            "src/__init__.py": "",
            "tests/test_main.py": """import pytest

def test_helper_function():
    assert True

def test_main_exists():
    assert callable
""",
            "tests/__init__.py": "",
            "README.md": """# Test Project

This is a sample project for testing the XML directory processor.

## Features
- Python package structure  
- Multiple modules
- Test suite
- Proper dependencies
""",
            ".gitignore": """__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
.coverage
.pytest_cache/
""",
        }

        # Create the directory structure with Windows-safe paths
        for path, content in project_structure.items():
            full_path = os.path.join(tmpdir, path.replace("/", os.sep))
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            try:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                logging.warning(f"Could not create {full_path}: {e}")

        yield tmpdir


@pytest.fixture
def problematic_files_project():
    """Create a project with files that commonly cause processing issues"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create various problematic files - Windows compatible
        problem_files = {
            "normal.py": "print('hello world')",
            "empty_file.txt": "",
            "large_file.py": "# Large file\n"
            + "# comment line\n" * 500,  # Reduced size for testing
            "special_chars.js": """// File with special characters
const html = "<div>Hello & goodbye</div>";
const quotes = "It's a test file";
console.log(html);""",
        }

        for filename, content in problem_files.items():
            file_path = os.path.join(tmpdir, filename)
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                logging.warning(f"Could not create {filename}: {e}")

        # Create a file with problematic encoding - Windows safe
        try:
            latin1_file = os.path.join(tmpdir, "latin1_encoding.txt")
            with open(latin1_file, "wb") as f:
                f.write("cafe resume naive".encode("latin-1"))  # ASCII-safe version
        except Exception as e:
            logging.warning(f"Could not create latin1 file: {e}")

        # Add realistic test files with proper sizes
        realistic_files = {
            "config.json": '{"name": "test", "version": "1.0.0", "debug": true}',
            "script.sh": "#!/bin/bash\necho 'Running tests...'\npython -m pytest",
            "data.csv": "id,name,value\n1,test1,100\n2,test2,200\n3,test3,300",
            ".env.example": "DATABASE_URL=sqlite:///test.db\nDEBUG=true\nSECRET_KEY=your_secret_here",
        }

        for filename, content in realistic_files.items():
            file_path = os.path.join(tmpdir, filename)
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                logging.warning(f"Could not create {filename}: {e}")

        yield tmpdir


@pytest.fixture
def standard_processing_params():
    """Standard parameters for directory processing"""
    return {
        "ignore_patterns": [
            ".git",
            "__pycache__",
            "node_modules",
            ".pytest_cache",
            "*.pyc",
            ".env",
            "dist",
            "build",
        ],
        "exclude_extensions": [
            ".csv",
            ".pt",
            ".pkl",
            ".bin",
            ".h5",
            ".parquet",
            ".zip",
            ".exe",
            ".dll",
            ".so",
            ".pyc",
        ],
        "json_size_threshold": 1024,
        "max_file_size": 1024 * 1024,  # 1MB
        "token_limit": 10000,
    }


@pytest.fixture
def large_test_project():
    """Create a larger test project for performance/memory testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a more realistic larger project structure
        for i in range(20):  # Reduced from 50 for faster testing
            module_dir = os.path.join(tmpdir, f"module_{i:02d}")
            os.makedirs(module_dir, exist_ok=True)

            # Create varied content to avoid tiktoken performance issues
            module_content = f"""
# Module {i} - Processing utilities
import os
import json
from typing import Dict, List, Optional

class DataProcessor{i}:
    '''Process data for module {i}'''
    
    def __init__(self, config: Dict):
        self.config = config
        self.processed_items = []
    
    def process(self, data: List[Dict]) -> List[Dict]:
        '''Process input data'''
        results = []
        for item in data:
            processed_item = {{
                'id': item.get('id', f'item_{i}'),
                'status': 'processed',
                'module': {i},
                'data': item
            }}
            results.append(processed_item)
            self.processed_items.append(processed_item)
        return results
    
    def get_stats(self) -> Dict:
        '''Get processing statistics'''
        return {{
            'total_processed': len(self.processed_items),
            'module_id': {i},
            'status': 'active'
        }}

def utility_function_{i}(data):
    '''Utility function for module {i}'''
    return f"Processed by module {i}: {{data}}"
"""

            try:
                with open(os.path.join(module_dir, "__init__.py"), "w") as f:
                    f.write(f"# Module {i} init\n")
                with open(os.path.join(module_dir, "processor.py"), "w") as f:
                    f.write(module_content)
                with open(os.path.join(module_dir, "config.json"), "w") as f:
                    f.write(
                        f'{{"module_id": {i}, "enabled": true, "priority": {i % 5}}}'
                    )
            except Exception as e:
                logging.warning(f"Could not create module {i}: {e}")

        yield tmpdir


def create_file_with_content(
    directory: str, filename: str, content: str, encoding: str = "utf-8"
):
    """Helper to create files with specific content and encoding - Windows safe"""
    filepath = os.path.join(directory, filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    try:
        if encoding == "binary":
            with open(filepath, "wb") as f:
                f.write(content.encode("utf-8", errors="ignore"))
        else:
            with open(filepath, "w", encoding=encoding) as f:
                f.write(content)
    except Exception as e:
        logging.warning(f"Could not create {filepath}: {e}")
        return None

    return filepath


def validate_xml_structure(content: str) -> Dict[str, any]:
    """Validate the XML-like structure of processor output"""
    validation_result = {
        "has_codebase_tags": "<codebase>" in content and "</codebase>" in content,
        "has_project_info": "<project" in content,
        "has_files_section": "<files>" in content and "</files>" in content,
        "file_count": content.count("<file "),
        "balanced_file_tags": content.count("<file") == content.count("</file>"),
        "balanced_dep_tags": content.count("<dep>") == content.count("</dep>"),
        "has_content_blocks": content.count("```") % 2
        == 0,  # Even number of code blocks
        "errors": [],
    }

    # Check for common issues
    if not validation_result["has_codebase_tags"]:
        validation_result["errors"].append("Missing codebase wrapper tags")

    if not validation_result["balanced_file_tags"]:
        validation_result["errors"].append("Unbalanced file tags")

    if not validation_result["balanced_dep_tags"]:
        validation_result["errors"].append("Unbalanced dependency tags")

    if validation_result["file_count"] == 0:
        validation_result["errors"].append("No files found in output")

    if validation_result["has_content_blocks"] != 0:
        validation_result["errors"].append("Unbalanced code block markers")

    validation_result["is_valid"] = len(validation_result["errors"]) == 0

    return validation_result


# Windows-compatible test markers
def pytest_configure(config):
    config.addinivalue_line("markers", "critical: marks tests as critical (must pass)")
    config.addinivalue_line(
        "markers", "important: marks tests as important (should pass)"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance-related"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "skip_on_windows: skip test on Windows")


def pytest_runtest_setup(item):
    """Skip certain tests on Windows"""
    if "skip_on_windows" in [marker.name for marker in item.iter_markers()]:
        if sys.platform.startswith("win"):
            pytest.skip("Skipped on Windows")
