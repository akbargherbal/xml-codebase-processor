"""
Enhanced directory processor optimized for LLM parsing and codebase recreation.
Key improvements:
1. Structured XML-like format for easy parsing
2. Embedded file metadata for recreation
3. Execution context hints
4. Dependency detection
5. Project structure inference
6. Windows compatibility and robust error handling

FIXES:
- Fixed XML tag balance bug in dependency section
- Improved error handling and logging
"""

import os
import sys
import argparse
import re
import tiktoken
import json
import logging
import hashlib
from tqdm import tqdm
from pathlib import Path
from typing import List, Dict, Tuple, Set, Optional
import nbconvert
import fnmatch

# Windows console encoding fix
if os.name == "nt":
    try:
        import codecs

        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")
    except:
        pass  # Fall back to default encoding

DEFAULT_OUTPUT_FILE = "codebase_structured.txt"
list_dir_ignored = []


def setup_logging(log_file: str, enable_logging: bool = True):
    if enable_logging:
        logging.basicConfig(
            filename=log_file,
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            filemode="w",
        )
    else:
        logging.basicConfig(level=logging.ERROR, handlers=[logging.NullHandler()])


def count_tokens(text: str) -> int:
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def detect_project_type(root_path: str) -> Dict[str, any]:
    """Detect project type and key files for LLM context with comprehensive error handling"""
    project_info = {
        "type": "unknown",
        "language": "mixed",
        "framework": None,
        "entry_points": [],
        "config_files": [],
        "dependency_files": [],
        "test_directories": [],
        "build_files": [],
    }

    # Check for key indicator files
    key_files = {
        "package.json": {"type": "nodejs", "language": "javascript"},
        "requirements.txt": {"type": "python", "language": "python"},
        "pyproject.toml": {"type": "python", "language": "python"},
        "setup.py": {"type": "python", "language": "python"},
        "Cargo.toml": {"type": "rust", "language": "rust"},
        "go.mod": {"type": "go", "language": "go"},
        "pom.xml": {"type": "java", "language": "java"},
        "build.gradle": {"type": "java", "language": "java"},
        "composer.json": {"type": "php", "language": "php"},
        "Gemfile": {"type": "ruby", "language": "ruby"},
    }

    try:
        for root, dirs, files in os.walk(root_path):
            if root.count(os.sep) - root_path.count(os.sep) > 2:  # Limit depth
                continue

            # Handle permission errors for directories
            try:
                accessible_files = files
                accessible_dirs = dirs
            except PermissionError:
                logging.warning(f"Permission denied accessing {root}")
                continue
            except Exception as e:
                logging.error(f"Error accessing directory {root}: {str(e)}")
                continue

            for file in accessible_files:
                try:
                    full_file_path = os.path.join(root, file)

                    # Check if file is accessible before processing
                    if not os.access(full_file_path, os.R_OK):
                        continue

                    if file in key_files:
                        info = key_files[file]
                        project_info.update(info)
                        project_info["dependency_files"].append(full_file_path)

                    # Config files
                    if file in [
                        "config.json",
                        "settings.py",
                        ".env.example",
                        "docker-compose.yml",
                        "Dockerfile",
                    ]:
                        project_info["config_files"].append(full_file_path)

                    # Entry points
                    if file in [
                        "main.py",
                        "app.py",
                        "index.js",
                        "server.js",
                        "main.go",
                        "main.rs",
                    ]:
                        project_info["entry_points"].append(full_file_path)

                    # Build files
                    if file in [
                        "Makefile",
                        "build.sh",
                        "webpack.config.js",
                        "vite.config.js",
                    ]:
                        project_info["build_files"].append(full_file_path)

                except Exception as e:
                    logging.warning(f"Error processing file {file} in {root}: {str(e)}")
                    continue

            # Test directories with error handling
            for dir_name in accessible_dirs:
                try:
                    if dir_name in ["test", "tests", "__tests__", "spec"]:
                        full_dir_path = os.path.join(root, dir_name)
                        if os.path.isdir(full_dir_path) and os.access(
                            full_dir_path, os.R_OK
                        ):
                            project_info["test_directories"].append(full_dir_path)
                except Exception as e:
                    logging.warning(
                        f"Error processing directory {dir_name} in {root}: {str(e)}"
                    )
                    continue

    except Exception as e:
        logging.error(f"Error during project type detection: {str(e)}")
        # Return basic project info even if detection fails

    return project_info


def get_file_metadata(file_path: str) -> Dict[str, any]:
    """Extract metadata useful for recreation"""
    try:
        stat = os.stat(file_path)
        ext = os.path.splitext(file_path)[1]

        metadata = {
            "size": stat.st_size,
            "extension": ext,
            "executable": os.access(file_path, os.X_OK),
            "relative_path": None,  # Will be set by caller
        }

        # Language-specific metadata
        if ext in [".py", ".js", ".ts", ".go", ".rs", ".java"]:
            metadata["is_source"] = True
        elif ext in [".json", ".yaml", ".yml", ".toml", ".ini"]:
            metadata["is_config"] = True
        elif ext in [".md", ".txt", ".rst"]:
            metadata["is_documentation"] = True
        elif ext in [".sh", ".bat", ".ps1"]:
            metadata["is_script"] = True
            metadata["executable"] = True

        return metadata
    except Exception:
        return {"size": 0, "extension": "", "executable": False}


def extract_imports_dependencies(content: str, file_path: str) -> List[str]:
    """Extract import statements for dependency mapping"""
    ext = os.path.splitext(file_path)[1].lower()
    imports = []

    try:
        if ext == ".py":
            import_patterns = [
                r"^import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)",
                r"^from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import",
            ]
        elif ext in [".js", ".ts"]:
            import_patterns = [
                r'^import.*from\s+[\'"]([^\'"]+)[\'"]',
                r'^const.*=\s*require\([\'"]([^\'"]+)[\'"]\)',
            ]
        elif ext == ".go":
            import_patterns = [r'^import\s+[\'"]([^\'"]+)[\'"]']
        else:
            return imports

        for pattern in import_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            imports.extend(matches)
    except Exception:
        pass

    return imports


def should_include_file(file_path: str, file_size: int, params: Dict) -> bool:
    ext = os.path.splitext(file_path)[1].lower()

    if ext in params["exclude_extensions"]:
        logging.debug(f"Excluded file due to extension: {file_path}")
        return False

    if ext == ".json" and file_size > params["json_size_threshold"]:
        logging.debug(f"Excluded JSON file due to size: {file_path}")
        return False

    if file_size > params["max_file_size"]:
        logging.debug(f"Excluded file due to size: {file_path}")
        return False

    return True


def should_ignore_path(path: str, ignore_patterns: List[str]) -> bool:
    path_parts = Path(path).parts

    for pattern in ignore_patterns:
        for part in path_parts:
            if pattern.endswith("/"):
                if part == pattern[:-1]:
                    return True
            else:
                if fnmatch.fnmatch(part, pattern) or pattern in part:
                    return True
    return False


def convert_notebook_to_markdown(notebook_path: str) -> str:
    logging.info(f"Converting notebook to markdown: {notebook_path}")
    markdown_exporter = nbconvert.MarkdownExporter()
    body, _ = markdown_exporter.from_filename(notebook_path)

    md_path = notebook_path.rsplit(".", 1)[0] + ".md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(body)

    logging.info(f"Notebook converted: {md_path}")
    return md_path


def safe_write_to_output(output_file, content: str):
    """Safely write content to output file with Windows encoding handling"""
    try:
        output_file.write(content)
    except UnicodeEncodeError:
        # Fallback for Windows console - replace problematic chars
        safe_content = content.encode("ascii", "replace").decode("ascii")
        output_file.write(safe_content)
        logging.warning(f"Content written with ASCII fallback due to encoding issues")


def process_directory_structured(
    root_path: str,
    params: Dict,
    output_file,
    project_info: Dict,
    excluded_files: List[Tuple[str, int]],
) -> None:
    """Process directory with structured XML-like output and comprehensive error handling"""

    # Write project header
    safe_write_to_output(output_file, "<codebase>\n")
    safe_write_to_output(
        output_file,
        f"<project type='{project_info['type']}' language='{project_info['language']}'>\n",
    )

    if project_info["entry_points"]:
        safe_write_to_output(output_file, "<entry_points>\n")
        for ep in project_info["entry_points"]:
            try:
                rel_ep = os.path.relpath(ep, root_path)
                safe_write_to_output(output_file, f"  <entry>{rel_ep}</entry>\n")
            except Exception as e:
                logging.error(f"Error processing entry point {ep}: {str(e)}")
        safe_write_to_output(output_file, "</entry_points>\n")

    if project_info["dependency_files"]:
        safe_write_to_output(output_file, "<dependencies>\n")
        for dep in project_info["dependency_files"]:
            try:
                rel_dep = os.path.relpath(dep, root_path)
                # FIXED: Use consistent XML tag naming - changed from <file> to <dep>
                safe_write_to_output(output_file, f"  <dep>{rel_dep}</dep>\n")
            except Exception as e:
                logging.error(f"Error processing dependency {dep}: {str(e)}")
        safe_write_to_output(output_file, "</dependencies>\n")

    if project_info["test_directories"]:
        safe_write_to_output(output_file, "<test_dirs>\n")
        for test_dir in project_info["test_directories"]:
            try:
                rel_test = os.path.relpath(test_dir, root_path)
                safe_write_to_output(output_file, f"  <dir>{rel_test}</dir>\n")
            except Exception as e:
                logging.error(f"Error processing test directory {test_dir}: {str(e)}")
        safe_write_to_output(output_file, "</test_dirs>\n")

    safe_write_to_output(output_file, "</project>\n\n")

    # Write files in structured format
    safe_write_to_output(output_file, "<files>\n")

    for root, dirs, files in os.walk(root_path):
        # Track and skip ignored directories with error handling
        original_dirs = dirs[:]
        dirs[:] = []
        for d in original_dirs:
            dir_path = os.path.join(root, d)
            try:
                if should_ignore_path(dir_path, params["ignore_patterns"]):
                    list_dir_ignored.append(dir_path)
                    logging.debug(f"Ignored directory: {dir_path}")
                else:
                    # Check if directory is accessible before adding to dirs
                    try:
                        os.listdir(dir_path)
                        dirs.append(d)
                    except PermissionError:
                        logging.error(
                            f"Permission denied accessing directory: {dir_path}"
                        )
                        try:
                            rel_path = os.path.relpath(dir_path, root_path)
                            safe_write_to_output(
                                output_file,
                                f"<directory path='{rel_path}' error='permission_denied'></directory>\n",
                            )
                        except:
                            pass  # Skip if path operations fail
                    except Exception as e:
                        logging.error(f"Error accessing directory {dir_path}: {str(e)}")
                        try:
                            rel_path = os.path.relpath(dir_path, root_path)
                            safe_write_to_output(
                                output_file,
                                f"<directory path='{rel_path}' error='access_failed'></directory>\n",
                            )
                        except:
                            pass
            except Exception as e:
                logging.error(f"Error processing directory {dir_path}: {str(e)}")
                continue

        for file in sorted(files):
            file_path = os.path.join(root, file)

            try:
                rel_path = os.path.relpath(file_path, root_path)
            except Exception as e:
                logging.error(f"Error getting relative path for {file_path}: {str(e)}")
                continue

            if should_ignore_path(file_path, params["ignore_patterns"]):
                list_dir_ignored.append(file_path)
                logging.debug(f"Ignored file: {file_path}")
                continue

            # Get file size with error handling
            try:
                file_size = os.path.getsize(file_path)
            except OSError as e:
                logging.error(f"Cannot access file: {file_path} - {str(e)}")
                try:
                    safe_write_to_output(
                        output_file,
                        f"<file path='{rel_path}' error='access_failed'></file>\n",
                    )
                except:
                    pass
                continue
            except Exception as e:
                logging.error(f"Error getting size for {file_path}: {str(e)}")
                try:
                    safe_write_to_output(
                        output_file,
                        f"<file path='{rel_path}' error='size_check_failed'></file>\n",
                    )
                except:
                    pass
                continue

            # Handle notebooks with comprehensive error handling
            original_file_path = file_path
            if file.endswith(".ipynb"):
                try:
                    md_path = convert_notebook_to_markdown(file_path)
                    file_path = md_path
                    rel_path = os.path.relpath(md_path, root_path)
                    file_size = os.path.getsize(md_path)
                    file = os.path.basename(md_path)
                except Exception as e:
                    logging.error(
                        f"Error converting notebook {original_file_path}: {str(e)}"
                    )
                    try:
                        safe_write_to_output(
                            output_file,
                            f"<file path='{rel_path}' error='notebook_conversion_failed'></file>\n",
                        )
                    except:
                        pass
                    continue

            if should_include_file(file_path, file_size, params):
                try:
                    metadata = get_file_metadata(file_path)
                    metadata["relative_path"] = rel_path

                    # Read file content with multiple encoding attempts
                    content = None
                    encodings_to_try = ["utf-8", "latin-1", "cp1252", "ascii"]
                    encoding_used = None

                    for encoding in encodings_to_try:
                        try:
                            with open(file_path, "r", encoding=encoding) as f:
                                content = f.read()
                                encoding_used = encoding
                            break
                        except (UnicodeDecodeError, UnicodeError):
                            continue
                        except (PermissionError, OSError) as e:
                            logging.error(f"Cannot read file {file_path}: {str(e)}")
                            break

                    if content is None:
                        # File could not be read with any encoding
                        try:
                            safe_write_to_output(
                                output_file,
                                f"<file path='{rel_path}' size='{file_size}' error='encoding_failed'></file>\n",
                            )
                        except:
                            pass
                        continue

                    if encoding_used != "utf-8":
                        logging.warning(
                            f"File {file_path} read with {encoding_used} encoding"
                        )

                    # Count tokens with error handling
                    try:
                        content_tokens = count_tokens(content)
                    except Exception as e:
                        logging.error(
                            f"Error counting tokens for {file_path}: {str(e)}"
                        )
                        content_tokens = len(content) // 4  # Rough estimate fallback

                    if content_tokens <= params["token_limit"]:
                        # Extract imports for dependency mapping
                        try:
                            imports = extract_imports_dependencies(content, file_path)
                        except Exception as e:
                            logging.warning(
                                f"Error extracting imports from {file_path}: {str(e)}"
                            )
                            imports = []

                        # Write structured file entry with Windows encoding safety
                        try:
                            file_header = f"<file path='{rel_path}' size='{file_size}' ext='{metadata['extension']}'"
                            if metadata.get("executable"):
                                file_header += " executable='true'"
                            if imports:
                                # Sanitize imports for XML attributes and Windows console
                                clean_imports = []
                                for imp in imports[:5]:
                                    try:
                                        clean_imp = imp.replace("'", "&apos;").replace(
                                            '"', "&quot;"
                                        )
                                        # Ensure ASCII compatibility for Windows
                                        clean_imp.encode("ascii", "ignore")
                                        clean_imports.append(clean_imp)
                                    except (UnicodeEncodeError, UnicodeError):
                                        # Skip problematic import names on Windows
                                        continue
                                if clean_imports:
                                    file_header += (
                                        f" imports='{','.join(clean_imports)}'"
                                    )
                            file_header += ">\n"

                            safe_write_to_output(output_file, file_header)

                            # Content with clear delimiters
                            safe_write_to_output(output_file, "```\n")
                            safe_write_to_output(output_file, content)
                            if not content.endswith("\n"):
                                safe_write_to_output(output_file, "\n")
                            safe_write_to_output(output_file, "```\n")
                            safe_write_to_output(output_file, "</file>\n\n")
                        except Exception as e:
                            logging.error(
                                f"Error writing content for {file_path}: {str(e)}"
                            )
                            try:
                                safe_write_to_output(
                                    output_file,
                                    f"<file path='{rel_path}' size='{file_size}' error='write_failed'></file>\n",
                                )
                            except:
                                pass
                    else:
                        try:
                            safe_write_to_output(
                                output_file,
                                f"<file path='{rel_path}' size='{file_size}' excluded='token_limit'></file>\n",
                            )
                        except:
                            pass
                        logging.info(
                            f"Content excluded due to token limit: {file_path}"
                        )

                except Exception as e:
                    logging.error(f"Error processing file {file_path}: {str(e)}")
                    try:
                        safe_write_to_output(
                            output_file,
                            f"<file path='{rel_path}' error='processing_failed'></file>\n",
                        )
                    except:
                        pass
            else:
                excluded_files.append((file_path, file_size))

    safe_write_to_output(output_file, "</files>\n")
    safe_write_to_output(output_file, "</codebase>\n")


def main():
    parser = argparse.ArgumentParser(
        description="Process directory for optimal LLM parsing and codebase recreation"
    )
    parser.add_argument("--enable-logging", action="store_true", default=False)
    parser.add_argument("directory_path", help="Path to the directory to process")
    parser.add_argument("--token-limit", type=int, default=10_000)
    parser.add_argument("--json-size-threshold", type=int, default=1024 * 1024)
    parser.add_argument(
        "--exclude-extensions",
        nargs="+",
        default=[
            ".csv",
            ".pt",
            ".pkl",
            ".bin",
            ".h5",
            ".parquet",
            ".gitignore",
            ".zip",
            ".exe",
            ".dll",
            ".so",
        ],
    )
    parser.add_argument(
        "--ignore-patterns",
        nargs="+",
        default=[
            ".env",
            ".git",
            ".history",
            ".idea",
            ".jest",
            ".pytest_cache",
            ".venv",
            ".vscode",
            "__pycache__",
            "assets",
            "bin",
            "bower_components",
            "build",
            "coverage",
            "dist",
            "document",
            "generated",
            "graphics",
            "images",
            "media",
            "migrations",
            "misc_docs",
            "node_modules",
            "obj",
            "packages",
            "public",
            "staticfiles",
            "tabs",
            "target",
            "test-results/",
            "LEGACY/",
            "/FastAPI",
            "SESSION_HANDOVER/",
            "utility_scripts/",
            "logs/",
            "staticfiles/",
            "vendor",
            "venv",
            "BUGS/",
            "TODO/",
            "TUTORIALS/",
            "QUIZ_COLLECTIONS/",
            "package-lock.json",
            DEFAULT_OUTPUT_FILE,
            "HTML_OUTPUT",
            "results_2025*",
        ],
    )
    parser.add_argument("--max-depth", type=int, default=10)
    parser.add_argument("--max-file-size", type=int, default=10 * 1024 * 1024)
    parser.add_argument("--output", default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--split-threshold", type=int, default=1000000)
    parser.add_argument("--log-file", default="directory_processing.log")

    args = parser.parse_args()

    setup_logging(args.log_file, args.enable_logging)
    logging.info("Starting enhanced directory processing")

    if not os.path.exists(args.directory_path) or not os.path.isdir(
        args.directory_path
    ):
        logging.error(f"Invalid directory: {args.directory_path}")
        print(f"Error: Invalid directory: {args.directory_path}")
        sys.exit(1)

    # Detect project structure
    project_info = detect_project_type(args.directory_path)
    logging.info(f"Detected project type: {project_info}")

    params = vars(args)
    excluded_files = []

    try:
        with open(args.output, "w", encoding="utf-8") as output_file:
            process_directory_structured(
                args.directory_path, params, output_file, project_info, excluded_files
            )
    except Exception as e:
        logging.error(f"Error during processing: {str(e)}")
        print(f"Error during processing: {str(e)}")
        sys.exit(1)

    # Token counting and splitting logic
    try:
        with open(args.output, "r", encoding="utf-8") as f:
            content = f.read()
            total_tokens = count_tokens(content)
    except Exception as e:
        logging.error(f"Error reading output file: {str(e)}")
        print(f"Error reading output file: {str(e)}")
        sys.exit(1)

    logging.info(f"Total tokens: {total_tokens}")
    print(f"Processing complete. Total tokens: {total_tokens}")

    # Show ignored directories/files like the original
    if list_dir_ignored:
        print("Ignored directories/files:")
        for ignored in list_dir_ignored[:10]:  # Limit output
            print(f"- {ignored}")
        if len(list_dir_ignored) > 10:
            print(f"... and {len(list_dir_ignored) - 10} more")

    # Show excluded files summary
    if excluded_files:
        print(f"\nExcluded {len(excluded_files)} files due to size/extension filters")
        if args.enable_logging:
            print(f"See {args.log_file} for detailed exclusion reasons")

    if total_tokens > args.split_threshold:
        logging.info("Output exceeds split threshold. Consider splitting.")
        print("Note: Output exceeds recommended token limit for single LLM context.")


if __name__ == "__main__":
    main()
