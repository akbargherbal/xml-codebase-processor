#!/usr/bin/env python3
"""
Codebase Skeleton Extractor
Generates LLM-optimized structural representations of codebases.
"""

import argparse
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional
from collections import defaultdict
import re

try:
    import tree_sitter_python as tspython
    import tree_sitter_javascript as tsjavascript
    import tree_sitter_typescript as tstypescript
    from tree_sitter import Language, Parser, Query, QueryCursor

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    print("Warning: tree-sitter not available, using fallback mode", file=sys.stderr)

try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print(
        "Warning: tiktoken not available, using approximate token counts",
        file=sys.stderr,
    )

try:
    from directory_tree import DisplayTree

    DIRECTORY_TREE_AVAILABLE = True
except ImportError:
    DIRECTORY_TREE_AVAILABLE = False
    print(
        "Warning: directory_tree not available, using basic tree display",
        file=sys.stderr,
    )


@dataclass
class Config:
    """Configuration for skeleton extraction."""

    mode: str = "skeleton"  # skeleton, overview, hybrid, custom
    include_full: Set[str] = field(default_factory=set)
    include_patterns: Set[str] = field(default_factory=set)
    skeleton_only: Set[str] = field(default_factory=set)
    exclude: Set[str] = field(default_factory=set)
    max_tokens: int = 50000
    show_deps: bool = False
    show_excluded: bool = False  # NEW LINE: Show detailed excluded directories list
    output: Optional[str] = None

    # Smart defaults
    DEFAULT_FULL_PATTERNS = {
        "README.md",
        "package.json",
        "requirements.txt",  # ← Added
        "setup.py",
        "setup.cfg",
        "pyproject.toml",  # ← Added
        "tsconfig.json",
        "docker-compose.yml",
        "Dockerfile",
        ".gitignore",
        ".dockerignore",
        "config.yaml",
    }

    DEFAULT_EXCLUDE_PATTERNS = {
        "node_modules",
        "venv",
        "env",
        ".env",
        ".venv",
        ".git",
        ".svn",
        ".hg",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "build",
        "dist",
        "target",
        ".next",
        ".nuxt",
        "coverage",
        ".coverage",
        "htmlcov",
        ".DS_Store",
        "Thumbs.db",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".Python",
        "*.so",
        "*.dylib",
        "*.dll",
        "*.egg",
        "*.egg-info",
        ".idea",
        ".vscode",
        "*.swp",
        "*.swo",
        ".pkl",
        ".parquet",
        # NOTE: .gitignore and .dockerignore are deliberately NOT in this list
        # They are config files in DEFAULT_FULL_PATTERNS and should be included
    }

    EXCLUDE_DIRS = {
        "tests",
        "test",
        "__tests__",
        "migrations",
        "db/migrate",
        "docs",
        "documentation",
        "examples",
        "samples",
        "static",
        "public",
        "assets",
        "media",
        "vendor",
        "third_party",
    }


class TokenCounter:
    """Token counting utility."""

    def __init__(self):
        if TIKTOKEN_AVAILABLE:
            self.encoder = tiktoken.get_encoding("cl100k_base")
        else:
            self.encoder = None

    def count(self, text: str) -> int:
        """Count tokens in text."""
        if self.encoder:
            return len(self.encoder.encode(text))
        # Rough approximation: 4 chars per token
        return len(text) // 4


class TreeBuilder:
    """Directory tree builder using directory_tree or fallback."""

    @staticmethod
    def build(root: Path, config: Config) -> str:
        """Build directory tree representation."""
        if DIRECTORY_TREE_AVAILABLE:
            try:
                # Build ignore list from config
                ignore_list = list(config.DEFAULT_EXCLUDE_PATTERNS | config.exclude)

                # Create DisplayTree instance
                tree = DisplayTree(str(root), ignoreList=ignore_list, stringRep=True)

                # DisplayTree returns string representation
                return str(tree)
            except Exception as e:
                print(
                    f"Warning: directory_tree failed: {e}, using fallback",
                    file=sys.stderr,
                )
                return TreeBuilder._fallback_tree(root, config)
        else:
            return TreeBuilder._fallback_tree(root, config)

    @staticmethod
    def _fallback_tree(root: Path, config: Config) -> str:
        """Fallback ASCII tree builder."""
        lines = [f"{root.name}/"]

        def should_ignore(path: Path) -> bool:
            """Check if path should be ignored in tree."""
            # Special case: Never ignore .gitignore or .dockerignore
            # These are config files we want to show
            if path.name in {".gitignore", ".dockerignore"}:
                return False

            # Check custom exclusions first (use name-based matching for simplicity)
            for pattern in config.exclude:
                # For patterns starting with '.', do exact name match
                if pattern.startswith("."):
                    if path.name == pattern:
                        return True
                # For wildcard patterns like "*.pyc"
                elif "*" in pattern:
                    if path.match(pattern):
                        return True
                # For other patterns, check if they match the name or any parent directory name
                else:
                    # Check if the pattern matches this path's name
                    if path.name == pattern:
                        return True
                    # Check if pattern appears in any parent directory name
                    try:
                        rel_path = path.relative_to(root)
                        if pattern in rel_path.parts:
                            return True
                    except ValueError:
                        # If we can't get relative path, check absolute path parts
                        if pattern in path.parts:
                            return True

            # Check default exclusions
            for pattern in config.DEFAULT_EXCLUDE_PATTERNS:
                # For patterns starting with '.', do exact name match
                if pattern.startswith("."):
                    if path.name == pattern:
                        return True
                # For wildcard patterns like "*.pyc"
                elif "*" in pattern:
                    if path.match(pattern):
                        return True
                # For other patterns, check if they match as directory/file names
                else:
                    # Check if pattern matches the name
                    if path.name == pattern:
                        return True
                    # Check if pattern appears in path hierarchy
                    try:
                        rel_path = path.relative_to(root)
                        if pattern in rel_path.parts:
                            return True
                    except ValueError:
                        if pattern in path.parts:
                            return True
            return False

        def add_dir(path: Path, prefix: str = "", depth: int = 0):
            # Limit depth to 5 levels (0-4)
            if depth >= 5:
                return

            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            except PermissionError:
                return

            # Filter items before processing
            items = [item for item in items if not should_ignore(item)]

            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current = "└── " if is_last else "├── "
                extension = "    " if is_last else "│   "

                if item.is_dir():
                    lines.append(f"{prefix}{current}{item.name}/")
                    add_dir(item, prefix + extension, depth + 1)
                else:
                    lines.append(f"{prefix}{current}{item.name}")

        add_dir(root)
        return "\n".join(lines)


class CodeExtractor:
    """Extracts code skeletons using Tree-sitter v0.21+ API."""

    def __init__(self):
        self.parsers = {}
        self.queries = {}
        if TREE_SITTER_AVAILABLE:
            self._init_parsers()

    def _init_parsers(self):
        """Initialize Tree-sitter parsers with v0.21+ API."""
        try:
            # Python
            PY_LANGUAGE = Language(tspython.language())
            self.parsers["python"] = Parser(PY_LANGUAGE)

            # Python queries for extraction
            self.queries["python"] = Query(
                PY_LANGUAGE,
                """
                (import_statement) @import
                (import_from_statement) @import
                (function_definition) @function
                (class_definition) @class
                """,
            )

            # JavaScript/TypeScript
            JS_LANGUAGE = Language(tsjavascript.language())
            self.parsers["javascript"] = Parser(JS_LANGUAGE)
            self.parsers["jsx"] = Parser(JS_LANGUAGE)

            # TypeScript
            TS_LANGUAGE = Language(tstypescript.language_typescript())
            self.parsers["typescript"] = Parser(TS_LANGUAGE)

            # TypeScript JSX
            TSX_LANGUAGE = Language(tstypescript.language_tsx())
            self.parsers["tsx"] = Parser(TSX_LANGUAGE)

            # Simplified query for all JS-family languages
            js_query_text = """
            (import_statement) @import
            (export_statement) @export
            (function_declaration) @function
            (arrow_function) @function
            (method_definition) @function
            (class_declaration) @class
            """

            self.queries["javascript"] = Query(JS_LANGUAGE, js_query_text)
            self.queries["jsx"] = Query(JS_LANGUAGE, js_query_text)
            self.queries["typescript"] = Query(TS_LANGUAGE, js_query_text)
            self.queries["tsx"] = Query(TSX_LANGUAGE, js_query_text)

        except Exception as e:
            print(f"Warning: Tree-sitter init failed: {e}", file=sys.stderr)
            self.parsers = {}
            self.queries = {}

    def extract_skeleton(self, file_path: Path, content: str) -> str:
        """Extract skeleton from file content."""
        ext = file_path.suffix.lstrip(".").lower()

        # Map extensions to parser types
        ext_map = {
            "py": "python",
            "js": "javascript",
            "jsx": "jsx",
            "ts": "typescript",
            "tsx": "tsx",
        }

        parser_type = ext_map.get(ext)

        if parser_type and parser_type in self.parsers:
            return self._extract_with_treesitter(content, parser_type)
        else:
            return self._fallback_extract(content, ext)

    def _extract_with_treesitter(self, content: str, parser_type: str) -> str:
        """Extract skeleton using Tree-sitter v0.21+ API."""
        try:
            source_bytes = bytes(content, "utf8")
            parser = self.parsers[parser_type]
            tree = parser.parse(source_bytes)

            if parser_type not in self.queries:
                return self._fallback_extract(content, parser_type)

            query = self.queries[parser_type]
            query_cursor = QueryCursor(query)

            # Use NEW API: captures() returns dict[str, list[Node]]
            captures = query_cursor.captures(tree.root_node)

            # Collect all nodes with their positions for sorting
            all_nodes = []

            if "import" in captures:
                for node in captures["import"]:
                    all_nodes.append(("import", node))

            if "export" in captures:
                for node in captures["export"]:
                    all_nodes.append(("export", node))

            if "function" in captures:
                for node in captures["function"]:
                    all_nodes.append(("function", node))

            if "class" in captures:
                for node in captures["class"]:
                    all_nodes.append(("class", node))

            # Sort by starting position to maintain source order
            all_nodes.sort(key=lambda x: x[1].start_byte)

            result = []
            lines = content.split("\n")
            last_import_idx = -1

            for idx, (node_type, node) in enumerate(all_nodes):
                if node_type == "import":
                    start_line = node.start_point[0]
                    end_line = node.end_point[0]
                    for i in range(start_line, end_line + 1):
                        if i < len(lines):
                            result.append(lines[i])
                    last_import_idx = idx

                elif node_type == "export":
                    # Add blank line after imports if this is first non-import
                    if last_import_idx == idx - 1:
                        result.append("")
                    start_line = node.start_point[0]
                    if start_line < len(lines):
                        result.append(lines[start_line])

                elif node_type == "function":
                    # Add blank line after imports if this is first non-import
                    if last_import_idx == idx - 1:
                        result.append("")
                    if parser_type == "python":
                        result.append(self._extract_function_python(node, lines))
                    else:
                        result.append(self._extract_function_js(node, source_bytes))

                elif node_type == "class":
                    # Add blank line after imports if this is first non-import
                    if last_import_idx == idx - 1:
                        result.append("")
                    if parser_type == "python":
                        result.append(self._extract_class_python(node, lines))
                    else:
                        result.append(self._extract_class_js(node, source_bytes))

            return (
                "\n".join(result)
                if result
                else self._fallback_extract(content, parser_type)
            )

        except Exception as e:
            print(f"Warning: Tree-sitter extraction failed: {e}", file=sys.stderr)
            return self._fallback_extract(content, parser_type)

    def _extract_function_python(self, func_node, lines: List[str]) -> str:
        """Extract Python function signature and docstring."""
        result = []

        # Extract signature (may span multiple lines)
        body_node = func_node.child_by_field_name("body")
        if not body_node:
            return lines[func_node.start_point[0]]  # Fallback

        signature_end_line = body_node.start_point[0]
        for i in range(func_node.start_point[0], signature_end_line):
            result.append(lines[i])

        # Add the line with colon
        last_sig_line = lines[signature_end_line]
        colon_pos = last_sig_line.find(":")
        if colon_pos != -1:
            result.append(last_sig_line[: colon_pos + 1])

        # Extract docstring if present
        if body_node.child_count > 0:
            first_child = body_node.children[0]
            if (
                first_child.type == "expression_statement"
                and first_child.child_count > 0
                and first_child.children[0].type == "string"
            ):
                docstring_node = first_child.children[0]
                doc_start = docstring_node.start_point[0]
                doc_end = docstring_node.end_point[0]
                for i in range(doc_start, doc_end + 1):
                    if i < len(lines):
                        result.append(lines[i])

        result.append("    # [Implementation hidden]\n")
        return "\n".join(result)

    def _extract_function_js(self, func_node, source_bytes: bytes) -> str:
        """Extract JS/TS function signature."""
        body_node = func_node.child_by_field_name("body")
        if body_node:
            # Extract from start to body start
            signature = (
                source_bytes[func_node.start_byte : body_node.start_byte]
                .decode("utf8", errors="ignore")
                .rstrip()
            )
            if not signature.endswith("{"):
                signature += " {"
            return signature + "\n    // [Implementation hidden]\n}\n"
        else:
            # Arrow function or other
            first_line = func_node.text.decode("utf8", errors="ignore").split("\n")[0]
            return first_line + " // [Implementation hidden]\n"

    def _extract_class_python(self, class_node, lines: List[str]) -> str:
        """Extract Python class definition with method signatures."""
        result = []

        # Class signature
        result.append(lines[class_node.start_point[0]])

        # Look for docstring and methods
        body_node = class_node.child_by_field_name("body")
        if body_node and body_node.child_count > 0:
            first_child = body_node.children[0]

            # Extract class docstring if present
            if (
                first_child.type == "expression_statement"
                and first_child.child_count > 0
                and first_child.children[0].type == "string"
            ):
                docstring_node = first_child.children[0]
                doc_start = docstring_node.start_point[0]
                doc_end = docstring_node.end_point[0]
                for i in range(doc_start, doc_end + 1):
                    if i < len(lines):
                        result.append(lines[i])
                result.append("")  # Blank line after docstring

            # Extract method signatures
            methods_found = False
            for child in body_node.children:
                if child.type == "function_definition":
                    methods_found = True
                    method_sig = self._extract_function_python(child, lines)
                    # Add proper indentation - methods should already be indented
                    result.append(method_sig)

            if not methods_found:
                result.append("    # [No methods defined]\n")

        return "\n".join(result)

    def _extract_class_js(self, class_node, source_bytes: bytes) -> str:
        """Extract JS/TS class definition with method signatures."""
        result = []

        # Class signature
        body_node = class_node.child_by_field_name("body")
        if body_node:
            signature = (
                source_bytes[class_node.start_byte : body_node.start_byte]
                .decode("utf8", errors="ignore")
                .rstrip()
            )
            if not signature.endswith("{"):
                signature += " {"
            result.append(signature)

            # Extract method signatures from class body
            methods_found = False
            for child in body_node.children:
                if child.type in ("method_definition", "field_definition"):
                    methods_found = True
                    # Get the method signature
                    method_text = child.text.decode("utf8", errors="ignore")
                    method_lines = method_text.split("\n")

                    # Extract signature (first line, possibly with params on multiple lines)
                    sig_lines = []
                    brace_count = 0
                    for line in method_lines:
                        sig_lines.append(line)
                        if "{" in line:
                            brace_count += line.count("{")
                            break

                    signature_text = "\n".join(sig_lines)
                    if "{" in signature_text:
                        signature_text = signature_text.split("{")[0].rstrip() + " {"

                    result.append("    " + signature_text)
                    result.append("        // [Implementation hidden]")
                    result.append("    }")
                    result.append("")  # Blank line between methods

            if not methods_found:
                result.append("    // [No methods defined]")

            result.append("}\n")
            return "\n".join(result)
        else:
            return class_node.text.decode("utf8", errors="ignore").split("\n")[0] + "\n"

    def _fallback_extract(self, content: str, ext: str = "") -> str:
        """AGGRESSIVE fallback extraction - signatures only."""
        lines = content.split("\n")
        result = []

        in_docstring = False
        docstring_char = None
        skip_until_next_def = False
        in_class = False
        class_indent = 0
        expect_class_docstring = False
        method_indent = 0  # Track method indentation for docstring detection

        for i, line in enumerate(lines):
            stripped = line.strip()
            current_indent = len(line) - len(line.lstrip())

            # Handle active docstrings first (highest priority)
            if in_docstring:
                result.append(line)
                # Check if docstring ends on this line
                if (
                    docstring_char
                    and stripped.endswith(docstring_char)
                    and stripped.count(docstring_char) >= 1
                ):
                    in_docstring = False
                    # After docstring ends, add implementation hidden marker
                    if in_class and method_indent > 0:
                        # For methods, use method indentation
                        result.append(
                            " " * (method_indent + 4) + "# [Implementation hidden]"
                        )
                        method_indent = 0  # Reset
                    else:
                        # For top-level functions
                        result.append("    # [Implementation hidden]\n")
                    docstring_char = None
                continue

            # Skip implementation after def/class until next def/class
            if skip_until_next_def and not in_class:
                # Check if we hit another def/class
                if any(
                    stripped.startswith(kw)
                    for kw in [
                        "def ",
                        "class ",
                        "function ",
                        "async def",
                        "async function",
                        "export function",
                        "export class",
                        "export const",
                    ]
                ):
                    skip_until_next_def = False
                    # Fall through to process this line
                else:
                    continue  # Skip implementation lines

            # Track if we're inside a class
            if stripped.startswith("class "):
                in_class = True
                class_indent = current_indent
                result.append(line)
                skip_until_next_def = False
                expect_class_docstring = True
                continue

            # Check for class docstring
            if expect_class_docstring:
                if stripped.startswith(('"""', "'''", "/*")):
                    in_docstring = True
                    expect_class_docstring = False
                    if stripped.startswith('"""'):
                        docstring_char = '"""'
                    elif stripped.startswith("'''"):
                        docstring_char = "'''"
                    elif stripped.startswith("/*"):
                        docstring_char = "*/"
                    result.append(line)
                    # Check if docstring ends on same line (single-line docstring)
                    if stripped.count(docstring_char) >= 2:
                        in_docstring = False
                        docstring_char = None
                    continue
                elif stripped and not stripped.startswith("#"):
                    # No docstring found, this is probably a method or other content
                    expect_class_docstring = False
                    # Fall through to process this line

            # Exit class when indentation decreases to class level or less
            if (
                in_class
                and stripped
                and current_indent <= class_indent
                and not stripped.startswith(("def ", "async def", "#", "@"))
            ):
                in_class = False

            # Inside a class, capture method signatures
            if in_class and any(
                stripped.startswith(kw) for kw in ["def ", "async def"]
            ):
                result.append(line.split("{")[0].rstrip())
                method_indent = current_indent  # Track for docstring processing
                # Check for method docstring on next line
                if i + 1 < len(lines):
                    next_line_stripped = lines[i + 1].strip()
                    if next_line_stripped.startswith(('"""', "'''")):
                        # Start tracking docstring
                        in_docstring = True
                        docstring_char = (
                            '"""' if next_line_stripped.startswith('"""') else "'''"
                        )
                        # Don't add implementation hidden yet - let docstring be processed
                    else:
                        # No docstring, add implementation hidden marker immediately
                        result.append(
                            " " * (current_indent + 4) + "# [Implementation hidden]"
                        )
                        method_indent = 0  # Reset
                continue

            # Imports (always include)
            if stripped.startswith(
                ("import ", "from ", "const ", "let ", "var ", "export ", "require(")
            ):
                result.append(line)
                continue

            # Function/class definitions (signature only) - top level only
            if not in_class and any(
                stripped.startswith(kw)
                for kw in [
                    "def ",
                    "function ",
                    "async def",
                    "async function",
                    "export function",
                    "export class",
                    "export const",
                ]
            ):
                # Just the signature line
                result.append(line.split("{")[0].rstrip())

                # Check for docstring start
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith(('"""', "'''", "/*")):
                        in_docstring = True
                        if next_line.startswith('"""'):
                            docstring_char = '"""'
                        elif next_line.startswith("'''"):
                            docstring_char = "'''"
                        elif next_line.startswith("/*"):
                            docstring_char = "*/"
                    else:
                        # No docstring, skip implementation
                        result.append("    # [Implementation hidden]\n")
                        skip_until_next_def = True
                continue

        # If we captured nothing, take first 5 lines as last resort
        if not result:
            if lines and any(line.strip() for line in lines):
                # File has content, take first 5 lines
                result = lines[:5]
                result.append("\n# [Rest of file hidden]")
            else:
                # Truly empty file
                result.append("# [Rest of file hidden]")

        return "\n".join(result)


class SkeletonGenerator:
    """Main skeleton generator."""

    def __init__(self, root_path: Path, config: Config):
        self.root = root_path
        self.config = config
        self.token_counter = TokenCounter()
        self.extractor = CodeExtractor()
        self.stats = {
            "files_processed": 0,
            "full_content": 0,
            "skeleton": 0,
            "excluded": 0,
            "total_tokens": 0,
        }

    ####

    def should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded."""
        rel_path = path.relative_to(self.root)
        # Normalize to forward slashes for cross-platform compatibility
        rel_path_str = str(rel_path).replace("\\", "/")

        # Check explicit exclusions
        for pattern in self.config.exclude:
            pattern_clean = pattern.rstrip("/")
            # Check if pattern appears in path
            if pattern_clean in rel_path_str:
                return True
            # Also try glob matching
            try:
                if rel_path.match(pattern):
                    return True
            except:
                pass

        # Check default exclusions
        for pattern in self.config.DEFAULT_EXCLUDE_PATTERNS:
            if rel_path.match(pattern) or any(
                p.match(pattern) for p in rel_path.parents
            ):
                return True
            if "*" not in pattern and pattern in rel_path.parts:
                return True

        # Check if in excluded directory name
        for part in rel_path.parts:
            if part in self.config.EXCLUDE_DIRS:
                return True

        return False

    def should_full_content(self, path: Path) -> bool:
        """Check if file should have full content."""
        # In hybrid mode, NOTHING gets full content except config files
        if self.config.mode == "hybrid":
            return path.name in self.config.DEFAULT_FULL_PATTERNS

        # Normalize path to use forward slashes for cross-platform compatibility
        rel_path_str = str(path.relative_to(self.root)).replace("\\", "/")

        # Explicit includes
        if rel_path_str in self.config.include_full:
            return True

        # Pattern matches
        for pattern in self.config.include_patterns:
            if path.match(pattern):
                return True

        # Default full content files (only in non-hybrid mode)
        if path.name in self.config.DEFAULT_FULL_PATTERNS:
            return True

        return False

    ####
    def generate(self) -> str:
        """Generate skeleton output."""
        output = []

        # Header
        output.append(f"<codebase project='{self.root.name}'>")
        output.append("\n<metadata>")

        # Directory tree
        output.append("<tree>")
        tree = TreeBuilder.build(self.root, self.config)
        output.append(tree)
        output.append("</tree>\n")

        # Collect files
        full_files = []
        skeleton_files = []
        excluded_dirs = defaultdict(int)

        for path in self.root.rglob("*"):
            if not path.is_file():
                continue

            # Check exclusion FIRST - excluded directories are completely ignored
            # regardless of file type or content
            if self.should_exclude(path):
                parent = path.parent.relative_to(self.root)
                # Normalize path for output
                parent_str = str(parent).replace("\\", "/")
                excluded_dirs[parent_str] += 1
                self.stats["excluded"] += 1
                continue  # Stop processing this file completely

            # Now check if remaining files need full content
            should_full = self.should_full_content(path)

            # Try to read the file
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                print(f"Warning: Could not read {path}: {e}", file=sys.stderr)
                # IMPORTANT: Skip this file entirely if it can't be read
                # Don't count it as processed, don't add it to output
                continue

            self.stats["files_processed"] += 1

            if should_full:
                full_files.append((path, content))
                self.stats["full_content"] += 1
            else:
                # Generate skeleton
                skeleton = self.extractor.extract_skeleton(path, content)
                skeleton_files.append((path, skeleton, len(content.split("\n"))))
                self.stats["skeleton"] += 1

        # Stats
        output.append("<stats>")
        output.append(f"Files processed: {self.stats['files_processed']}")
        output.append(f"Full content: {self.stats['full_content']} files")
        output.append(f"Skeleton: {self.stats['skeleton']} files")
        output.append(f"Excluded: {self.stats['excluded']} files")
        if TREE_SITTER_AVAILABLE and self.extractor.parsers:
            output.append("Tree-sitter: enabled")
        else:
            output.append("Tree-sitter: disabled (using fallback)")
        output.append("</stats>")
        output.append("</metadata>\n")

        # Full content files
        if full_files and self.config.mode != "overview":
            output.append("<full-content>")
            for path, content in full_files:
                rel_path = path.relative_to(self.root)
                # Normalize path for output (forward slashes)
                rel_path_str = str(rel_path).replace("\\", "/")
                tokens = self.token_counter.count(content)
                self.stats["total_tokens"] += tokens

                output.append(f"\n<file path='{rel_path_str}' tokens='{tokens}'>")
                output.append(content)
                output.append("</file>")
            output.append("\n</full-content>\n")

        # Skeleton files
        if skeleton_files and self.config.mode in ("skeleton", "hybrid", "custom"):
            output.append("<skeleton>")
            for path, skeleton, loc in skeleton_files:
                rel_path = path.relative_to(self.root)
                # Normalize path for output (forward slashes)
                rel_path_str = str(rel_path).replace("\\", "/")
                tokens = self.token_counter.count(skeleton)
                self.stats["total_tokens"] += tokens

                output.append(
                    f"\n<file path='{rel_path_str}' loc='{loc}' tokens='{tokens}'>"
                )
                output.append(skeleton)
                output.append("</file>")
            output.append("\n</skeleton>\n")

        # Excluded summary (optional, controlled by --show-excluded flag)
        if excluded_dirs and self.config.show_excluded:
            output.append("<excluded>")
            for dir_path, count in sorted(excluded_dirs.items()):
                output.append(f"<directory path='{dir_path}' files='{count}'/>")
            output.append("</excluded>\n")

        output.append(f"\n<total-tokens>{self.stats['total_tokens']}</total-tokens>")
        output.append("</codebase>")

        return "\n".join(output)


###


def main():
    parser = argparse.ArgumentParser(
        description="Generate LLM-optimized codebase skeletons",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ~/my-project
  %(prog)s ~/my-project --mode=overview
  %(prog)s ~/my-project --output=skeleton.txt
  %(prog)s ~/my-project --include-full="src/auth/models.py"
  %(prog)s ~/my-project --exclude="vendor/,legacy/"

Install optional dependencies:
  pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-typescript
  pip install tiktoken directory-tree
        """,
    )

    parser.add_argument("path", type=str, help="Path to codebase root")
    parser.add_argument(
        "--mode",
        choices=["skeleton", "overview", "hybrid", "custom"],
        default="skeleton",
        help="Output mode (default: skeleton)",
    )
    parser.add_argument(
        "--include-full",
        type=str,
        default="",
        help="Comma-separated files for full content",
    )
    parser.add_argument(
        "--include-patterns",
        type=str,
        default="",
        help="Comma-separated patterns for full content",
    )
    parser.add_argument(
        "--skeleton-only",
        type=str,
        default="",
        help="Comma-separated directories for skeleton only",
    )
    parser.add_argument(
        "--exclude", type=str, default="", help="Comma-separated patterns to exclude"
    )

    parser.add_argument(
        "--max-tokens", type=int, default=50000, help="Maximum token budget"
    )
    parser.add_argument(
        "--show-deps", action="store_true", help="Show dependency graph (future)"
    )
    parser.add_argument(
        "--show-excluded",
        action="store_true",
        help="Include detailed excluded directories list in output (default: False)",
    )

    parser.add_argument("--output", type=str, help="Output file (default: stdout)")

    args = parser.parse_args()

    # Build config
    config = Config(
        mode=args.mode,
        max_tokens=args.max_tokens,
        show_deps=args.show_deps,
        output=args.output,
    )

    if args.include_full:
        config.include_full = set(args.include_full.split(","))
    if args.include_patterns:
        config.include_patterns = set(args.include_patterns.split(","))
    if args.skeleton_only:
        config.skeleton_only = set(args.skeleton_only.split(","))
    if args.exclude:
        config.exclude = set(args.exclude.split(","))

    # Generate
    root_path = Path(args.path).resolve()
    if not root_path.exists():
        print(f"Error: Path does not exist: {root_path}", file=sys.stderr)
        sys.exit(1)

    if not root_path.is_dir():
        print(f"Error: Path is not a directory: {root_path}", file=sys.stderr)
        sys.exit(1)

    generator = SkeletonGenerator(root_path, config)
    output = generator.generate()

    # Write output
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"✅ Skeleton written to {args.output}")
        print(f"📊 Stats:")
        print(f"  - Files processed: {generator.stats['files_processed']}")
        print(f"  - Full content: {generator.stats['full_content']}")
        print(f"  - Skeleton: {generator.stats['skeleton']}")
        print(f"  - Total tokens: {generator.stats['total_tokens']}")
    else:
        print(output)


if __name__ == "__main__":
    main()
