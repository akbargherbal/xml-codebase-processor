# XML Codebase Processor

A Python tool to process directories into a structured XML-like format optimized for Large Language Model (LLM) parsing and codebase recreation. It extracts file metadata, dependencies, and project structure while handling diverse file types, encodings, and platform-specific challenges (e.g., Windows compatibility).

## Features

- **Structured Output**: Generates XML-like output with file contents, metadata (size, extension, executable status), and project details (type, language, entry points).
- **Robust Error Handling**: Gracefully manages encoding issues, permission errors, and broken symlinks.
- **Dependency Detection**: Identifies imports and dependencies for Python, JavaScript, Go, and more.
- **Project Type Inference**: Detects project types (e.g., Python, Node.js, Java) via key files like `requirements.txt` or `package.json`.
- **Comprehensive Testing**: Includes a pytest-based suite with critical, important, and integration tests to ensure reliability.
- **Windows Compatibility**: Handles platform-specific encoding and filesystem quirks.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/xml-codebase-processor.git
   cd xml-codebase-processor
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   Required packages: `tiktoken`, `nbconvert`, `tqdm`, `pytest`, `psutil`.

## Usage

Run the processor on a directory:
```bash
python xml_directory_processor.py /path/to/directory --output codebase_output.txt
```

### Command-Line Options
- `--directory_path`: Path to the directory to process (required).
- `--output`: Output file path (default: `codebase_structured.txt`).
- `--token-limit`: Maximum tokens per file (default: 10,000).
- `--json-size-threshold`: Max size for JSON files (default: 1MB).
- `--exclude-extensions`: Extensions to skip (e.g., `.csv`, `.zip`).
- `--ignore-patterns`: Directories/files to ignore (e.g., `.git`, `node_modules`).
- `--enable-logging`: Enable detailed logging to a file.
- `--log-file`: Log file path (default: `directory_processing.log`).

Example:
```bash
python xml_directory_processor.py ./my_project --token-limit 5000 --exclude-extensions .csv .bin --enable-logging
```

## Testing

The project includes a robust test suite using pytest, with prioritized phases (critical, important, integration, validation).

Run all tests:
```bash
pytest -v
```

Run critical tests only (fast feedback):
```bash
python quick_test_runner.py
```

Run full test suite with logging:
```bash
python run_tests.py --verbose
```

### Test Structure
- **Critical**: Encoding, filesystem, and memory tests (must pass for production).
- **Important**: Project detection, token counting, and XML output integrity.
- **Integration**: End-to-end project processing and import extraction.
- **Validation**: Edge cases like large files, deep directories, and filtering.

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature-name`.
3. Commit changes: `git commit -m "Add feature"`.
4. Push to the branch: `git push origin feature-name`.
5. Open a pull request.

Please include tests for new features and ensure coverage remains above 80% (enforced via `pytest-cov`).

## Development Notes
- **Codebase**: Main logic in `xml_directory_processor.py`. Test runners in `quick_test_runner.py` and `run_tests.py`.
- **Tests**: Located in `tests/` with subdirectories for critical, important, integration, and validation tests.
- **Dependencies**: Managed via `requirements.txt`. Key libraries: `tiktoken` (token counting), `nbconvert` (notebook conversion), `pytest` (testing).
- **Platform**: Tested on Python 3.12, with Windows compatibility.

## License

MIT License. See [LICENSE](LICENSE) for details.
