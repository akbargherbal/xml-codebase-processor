# XML Directory Processor

A powerful Python tool that converts directory structures and file contents into structured XML-like format, optimized for Large Language Model (LLM) parsing and codebase recreation.

## Features

- **Structured XML-like output** for easy LLM parsing
- **Embedded file metadata** (size, type, permissions, imports)
- **Project type detection** (Python, Node.js, Rust, Go, Java, etc.)
- **Dependency mapping** with import extraction
- **Token counting** for LLM context management
- **Jupyter notebook conversion** to markdown
- **Comprehensive error handling** with detailed logging
- **Windows compatibility** with encoding safeguards
- **🆕 Flexible filtering** with `--include` and `--exclude` flags

## Installation

### Requirements

```bash
Python 3.9+
```

### Dependencies

```bash
pip install tiktoken nbconvert tqdm
```

Or install all dependencies at once:

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

Process entire directory with default settings:

```bash
python xml_directory_processor.py /path/to/your/project
```

Specify output file:

```bash
python xml_directory_processor.py /path/to/your/project --output my_codebase.txt
```

### 🆕 Filtering with Include/Exclude

**Include only specific directories:**

```bash
# Process only the src directory
python xml_directory_processor.py . --include src --output src_only.txt

# Process multiple directories
python xml_directory_processor.py . --include src tests --output code.txt

# Comma-separated syntax also works
python xml_directory_processor.py . --include src,tests --output code.txt
```

**Include only specific file types:**

```bash
# Process only Python files
python xml_directory_processor.py . --include "*.py" --output python_files.txt

# Process only documentation
python xml_directory_processor.py . --include "*.md,*.rst,docs" --output docs.txt
```

**Exclude additional directories:**

```bash
# Exclude directories beyond the defaults
python xml_directory_processor.py . --exclude examples,tutorials --output clean_code.txt

# Exclude specific file patterns
python xml_directory_processor.py . --exclude "*.log,*.tmp,cache" --output code.txt
```

**Combine include and exclude:**

```bash
# Process src but exclude test fixtures and cache
python xml_directory_processor.py . \
  --include src \
  --exclude fixtures,__pycache__,"*.pyc" \
  --output production_src.txt
```

## Command-Line Options

### Core Options

| Option             | Description                  | Default                    |
| ------------------ | ---------------------------- | -------------------------- |
| `directory_path`   | Path to directory to process | (required)                 |
| `--output`         | Output file path             | `codebase_structured.txt`  |
| `--enable-logging` | Enable detailed logging      | `False`                    |
| `--log-file`       | Log file path                | `directory_processing.log` |

### 🆕 Filtering Options

| Option              | Description                                    | Example                               |
| ------------------- | ---------------------------------------------- | ------------------------------------- |
| `--include`         | Patterns to include (space or comma-separated) | `--include src tests`                 |
| `--exclude`         | Additional patterns to exclude                 | `--exclude docs,examples`             |
| `--ignore-patterns` | Base ignore patterns (can override defaults)   | `--ignore-patterns .git node_modules` |

### File Filtering

| Option                  | Description                | Default                    |
| ----------------------- | -------------------------- | -------------------------- |
| `--token-limit`         | Max tokens per file        | `10,000`                   |
| `--max-file-size`       | Max file size in bytes     | `10MB`                     |
| `--json-size-threshold` | Max JSON file size         | `1MB`                      |
| `--exclude-extensions`  | File extensions to exclude | `.csv .pkl .bin .exe` etc. |

### Advanced Options

| Option              | Description                       | Default     |
| ------------------- | --------------------------------- | ----------- |
| `--max-depth`       | Maximum directory depth           | `10`        |
| `--split-threshold` | Token threshold for split warning | `1,000,000` |

## Use Cases

### 1. Code Review Preparation

Process only source code for review:

```bash
python xml_directory_processor.py . \
  --include src \
  --exclude __pycache__,"*.pyc",test_fixtures \
  --output code_review.txt
```

### 2. Documentation Analysis

Extract only documentation files:

```bash
python xml_directory_processor.py . \
  --include "*.md,*.rst,docs" \
  --output documentation.txt
```

### 3. Specific Module Analysis

Analyze a specific part of a large monorepo:

```bash
python xml_directory_processor.py /large/monorepo \
  --include services/api,services/web \
  --exclude node_modules,build \
  --output api_and_web.txt
```

### 4. Migration Planning

Process old and new code separately:

```bash
# Legacy code
python xml_directory_processor.py . \
  --include legacy \
  --output legacy_code.txt

# New implementation
python xml_directory_processor.py . \
  --include src \
  --exclude legacy \
  --output new_code.txt
```

### 5. Full Codebase with Custom Exclusions

```bash
python xml_directory_processor.py . \
  --exclude results,output,temp,generated \
  --enable-logging \
  --output full_codebase.txt
```

## Output Format

The tool generates structured XML-like output:

```xml
<codebase>
<project type='python' language='python'>
<entry_points>
  <entry>main.py</entry>
</entry_points>
<dependencies>
  <dep>requirements.txt</dep>
</dependencies>
<test_dirs>
  <dir>tests</dir>
</test_dirs>
</project>

<files>
<file path='src/main.py' size='1234' ext='.py' imports='os,sys,argparse'>
```

def main():
pass

```
</file>
</files>
</codebase>
```

## Default Ignore Patterns

The following patterns are ignored by default (can be extended with `--exclude`):

- **Version Control:** `.git`, `.history`
- **Virtual Environments:** `venv`, `.venv`, `node_modules`
- **Build Artifacts:** `build`, `dist`, `target`, `bin`, `obj`
- **Cache Directories:** `__pycache__`, `.pytest_cache`, `coverage`, `htmlcov`
- **IDE Folders:** `.idea`, `.vscode`
- **Dependencies:** `vendor`, `packages`, `bower_components`
- **Generated Files:** `generated`, `migrations`, `staticfiles`
- **Media:** `assets`, `images`, `graphics`, `media`
- **Lock Files:** `package-lock.json`

## Testing

### Run All Tests

```bash
pytest tests/ --cov=xml_directory_processor --cov-report=term-missing -v
```

### Run Specific Test Suites

```bash
# Critical tests (encoding, filesystem, memory)
pytest tests/critical/ -v

# Important tests (project detection, token counting, XML output)
pytest tests/important/ -v

# Integration tests (full processing, import extraction)
pytest tests/integration/ -v

# Validation tests (file filtering, performance)
pytest tests/validation/ -v

# Unit tests for new filtering features
pytest tests/unit/ -v
```

### Generate Coverage Report

```bash
# Terminal output with missing lines
pytest --cov=xml_directory_processor --cov-report=term-missing

# HTML report (opens in browser)
pytest --cov=xml_directory_processor --cov-report=html
open htmlcov/index.html
```

### Quick Test

Test the new include/exclude functionality:

```bash
# Test include
python xml_directory_processor.py . --include tests --output test_include.txt

# Test exclude
python xml_directory_processor.py . --exclude tests --output test_exclude.txt

# Verify both outputs are different
wc -l test_include.txt test_exclude.txt
```

## Project Structure

```
xml-codebase-processor/
├── xml_directory_processor.py       # Main script
├── README.md                         # This file
├── requirements.txt                  # Dependencies
├── tests/
│   ├── critical/                     # Critical path tests
│   │   ├── test_encoding_handling.py
│   │   ├── test_filesystem_access.py
│   │   └── test_memory_management.py
│   ├── important/                    # Important functionality tests
│   │   ├── test_project_detection.py
│   │   ├── test_token_counting.py
│   │   └── test_xml_output.py
│   ├── integration/                  # Integration tests
│   │   ├── test_full_processing.py
│   │   ├── test_import_extraction.py
│   │   └── test_include_exclude_integration.py  # 🆕 New filtering tests
│   ├── validation/                   # Validation tests
│   │   ├── test_file_filtering.py
│   │   └── test_performance_edge_cases.py
│   └── unit/                         # 🆕 Unit tests
│       └── test_pattern_processing.py
└── htmlcov/                          # Coverage reports (generated)
```

## Performance Considerations

### Large Codebases

For projects with many files (>1000):

1. **Use include filters** to process specific directories
2. **Enable logging** to track progress: `--enable-logging`
3. **Process in chunks** if token limit exceeded

```bash
# Process different sections separately
python xml_directory_processor.py . --include src/frontend --output frontend.txt
python xml_directory_processor.py . --include src/backend --output backend.txt
python xml_directory_processor.py . --include tests --output tests.txt
```

### Token Management

If output exceeds LLM context limits:

```bash
# The tool will suggest splitting when tokens > 1,000,000
# Follow the suggestions to process directories separately
```

### Memory Usage

For very large files or projects:

- Adjust `--max-file-size` to skip large files
- Use `--token-limit` to exclude long files
- Process specific directories with `--include`

## Troubleshooting

### Common Issues

**1. Permission Errors**

```bash
# Enable logging to see which files/directories are inaccessible
python xml_directory_processor.py . --enable-logging
cat directory_processing.log | grep "Permission denied"
```

**2. Encoding Errors**

The tool automatically tries multiple encodings (utf-8, latin-1, cp1252, ascii). Check logs for files that failed to decode.

**3. Large Output Files**

```bash
# Use include filters to reduce output size
python xml_directory_processor.py . --include src --output smaller.txt

# Check token count
python -c "
import tiktoken
enc = tiktoken.get_encoding('cl100k_base')
with open('codebase_structured.txt') as f:
    print(f'Tokens: {len(enc.encode(f.read())):,}')
"
```

**4. Missing Dependencies**

```bash
# Install all requirements
pip install -r requirements.txt

# Or install individually
pip install tiktoken nbconvert tqdm pytest pytest-cov
```

### Debug Mode

```bash
# Enable detailed logging
python xml_directory_processor.py . \
  --enable-logging \
  --log-file debug.log \
  --output test.txt

# Review the log
cat debug.log
```

## Advanced Usage

### Custom Ignore Patterns

Override default ignore patterns completely:

```bash
python xml_directory_processor.py . \
  --ignore-patterns ".git" "node_modules" "*.pyc" \
  --output custom_ignores.txt
```

### Pattern Syntax

Patterns support:

- **Exact names:** `node_modules`, `.git`
- **Wildcards:** `*.pyc`, `test_*`, `*.log`
- **Paths:** `src/generated`, `tests/fixtures`

### Combining Multiple Filters

```bash
python xml_directory_processor.py /path/to/project \
  --include "src,lib" \
  --exclude "generated,*.min.js" \
  --exclude-extensions ".csv,.pkl,.bin" \
  --max-file-size 5242880 \
  --token-limit 5000 \
  --output filtered.txt
```

## Integration with LLMs

### Claude/GPT Usage

```bash
# Generate codebase file
python xml_directory_processor.py . --output codebase.txt

# Upload to Claude or paste into GPT
# Prompt: "Analyze this codebase and suggest improvements..."
```

### Chunking for Large Projects

```bash
# Split by component
python xml_directory_processor.py . --include frontend --output frontend.txt
python xml_directory_processor.py . --include backend --output backend.txt

# Process each chunk separately with LLM
```

## Contributing

### Running Tests Before Contributing

```bash
# Run all tests
pytest tests/ -v

# Check coverage (should be >60%)
pytest --cov=xml_directory_processor --cov-report=term-missing

# Run specific test categories
pytest tests/critical/ -v           # Must pass
pytest tests/important/ -v          # Must pass
pytest tests/integration/ -v        # Must pass
pytest tests/validation/ -v         # Should pass
pytest tests/unit/ -v               # Should pass
```

### Test Coverage Goals

- **Critical tests:** 100% must pass
- **Important tests:** 100% must pass
- **Overall coverage:** >60% (target: 70%)
- **New features:** Require tests before merge

## Changelog

### Version 2.0.0 (Latest)

- 🆕 Added `--include` flag for selective directory processing
- 🆕 Added `--exclude` flag for additional exclusions
- 🆕 Support for comma-separated and space-separated patterns
- 🆕 Comprehensive test suite with 100+ tests
- ✨ Improved filtering performance with early directory skipping
- ✨ Enhanced help messages and usage examples
- ✨ Better output summary with filter information
- 🐛 Fixed XML tag balance in dependency section
- 📚 Updated documentation with new features

### Version 1.x

- Initial release with basic functionality
- Project type detection
- Token counting
- Jupyter notebook support
- Windows compatibility

## License

[Your License Here]

## Support

For issues, questions, or contributions:

- Check the troubleshooting section above
- Enable logging with `--enable-logging` for detailed diagnostics
- Review test files for usage examples
- Open an issue with logs and reproduction steps

## Examples Repository

See the `examples/` directory (if available) for:

- Sample outputs for different project types
- Advanced filtering recipes
- Integration scripts for CI/CD
- LLM prompt templates

---

**Quick Reference Card:**

```bash
# Basic
python xml_directory_processor.py .

# Source only
python xml_directory_processor.py . --include src

# Docs only
python xml_directory_processor.py . --include "*.md,docs"

# Exclude temp files
python xml_directory_processor.py . --exclude temp,cache,logs

# Debug
python xml_directory_processor.py . --enable-logging

# Run tests
pytest tests/ -v
```
