import pytest
from xml_directory_processor import extract_imports_dependencies

@pytest.mark.integration
class TestImportExtraction:
    """Test import/dependency extraction functionality"""

    def test_python_import_extraction(self):
        """Test extraction of Python imports"""
        python_code = """import os\nfrom pathlib import Path\nimport xml.etree.ElementTree as ET"""
        imports = extract_imports_dependencies(python_code, "test.py")
        expected = ["os", "pathlib", "xml.etree.ElementTree"]
        for exp in expected:
            assert any(exp in imp for imp in imports)

    def test_javascript_import_extraction(self):
        """Test extraction of JavaScript imports"""
        js_code = """import React from 'react';\nconst fs = require('fs');"""
        imports = extract_imports_dependencies(js_code, "test.js")
        expected = ["react", "fs"]
        for exp in expected:
            assert any(exp in imp for imp in imports)