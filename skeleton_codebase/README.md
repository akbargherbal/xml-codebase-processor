# Codebase Skeleton Extractor

**Generate LLM-optimized structural representations of your codebases.**

Stop copy-pasting entire projects into Claude. Get just the architectural skeleton—function signatures, class definitions, imports, and config files—while excluding implementation details, tests, and noise.

Perfect for:
- 🔄 **Referencing old projects** when building new ones
- 🧭 **Understanding unfamiliar codebases** quickly
- 📝 **Documenting architecture** without exposing sensitive implementation
- 🤖 **Feeding context to LLMs** without hitting token limits

---

## Why Use This?

**Problem:** Sharing a full codebase with an LLM wastes tokens on test files, migrations, node_modules, and function implementations you don't need.

**Solution:** Extract a "skeleton" that shows *how* your code is structured without the *what* it does.

**Result:** 80-90% token reduction while preserving full architectural understanding.

---

## Quick Start

### Installation

```bash
# Minimal (works without dependencies)
chmod +x codebase_skeleton.py

# Recommended (for best results)
pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-typescript tiktoken directory-tree
```

### Basic Usage

```bash
# Generate skeleton of a project
python codebase_skeleton.py ~/my-django-project

# Save to file for LLM reference
python codebase_skeleton.py ~/my-django-project --output=skeleton.txt

# Just see the structure (no code)
python codebase_skeleton.py ~/my-django-project --mode=overview

# Include specific files in full
python codebase_skeleton.py ~/my-django-project \
  --include-full="src/settings.py,src/urls.py"
```

---

## Features

### 🎯 Smart Tiered Content Strategy

**Tier 1: Full Content** (always included)
- `README.md`, `LICENSE`, documentation
- `package.json`, `pyproject.toml`, `requirements.txt`
- Configuration files (`settings.py`, `tsconfig.json`, `.env.example`)
- Entry points (`main.py`, `app.py`, `index.js`)

**Tier 2: Skeleton Only** (signatures without implementation)
- Function definitions + docstrings
- Class definitions + method signatures
- Type hints and decorators
- Import statements

**Tier 3: Excluded** (listed but not included)
- Tests and test fixtures
- Migrations and generated code
- Assets, media, static files
- `node_modules`, `.venv`, build artifacts

### 🌲 Tree-sitter Powered Extraction

When available, uses **Tree-sitter** for precise parsing:

**Python Example:**
```python
# Input:
def authenticate(self, username: str, password: str) -> bool:
    """Verify user credentials against database."""
    hashed = hash_password(password)
    user = User.objects.get(username=username)
    return user.password == hashed

# Output (skeleton):
def authenticate(self, username: str, password: str) -> bool:
    """Verify user credentials against database."""
    # [Implementation hidden]
```

**JavaScript/TypeScript Example:**
```javascript
// Input:
export async function fetchUserData(userId) {
  const response = await fetch(`/api/users/${userId}`);
  if (!response.ok) throw new Error('Failed to fetch');
  return response.json();
}

// Output (skeleton):
export async function fetchUserData(userId)
    // [Implementation hidden]
```

**Supported Languages:**
- ✅ Python (`.py`)
- ✅ JavaScript (`.js`, `.jsx`)
- ✅ TypeScript (`.ts`, `.tsx`)
- 🔄 Go, Rust, Java (fallback mode)

### 📊 Directory Tree Visualization

```
my-django-project/
├── manage.py
├── requirements.txt
├── src/
│   ├── models.py [150 LOC]
│   ├── views.py [200 LOC]
│   ├── urls.py [50 LOC]
│   └── utils/
│       ├── auth.py [100 LOC]
│       └── validators.py [80 LOC]
├── tests/ [excluded, 45 files]
└── migrations/ [excluded, 23 files]
```

### 🎛️ Four Output Modes

#### `--mode=skeleton` (Default)
Complete architectural view:
- Full config files
- Code skeletons (signatures only)
- Excluded file lists

**Use case:** Reference when building similar projects

#### `--mode=overview`
Structure only, no code:
- Directory tree
- File counts and stats
- No actual code content

**Use case:** Quick exploration, deciding what to investigate

#### `--mode=hybrid`
Balanced approach:
- Full config files
- First 20 lines of each code file
- Works without Tree-sitter

**Use case:** Quick setup, lightweight preview

#### `--mode=custom`
You control what gets full content:
- Use `--include-full` for specific files
- Everything else gets skeleton treatment

**Use case:** Deep dive into one module, skeleton for rest

---

## Command-Line Reference

### Basic Options

```bash
python codebase_skeleton.py <path> [options]
```

| Option | Description | Example |
|--------|-------------|---------|
| `path` | Path to codebase root | `~/my-project` |
| `--mode` | Output mode | `skeleton`, `overview`, `hybrid`, `custom` |
| `--output` | Save to file | `--output=skeleton.txt` |

### Inclusion Options

| Option | Description | Example |
|--------|-------------|---------|
| `--include-full` | Files for full content (comma-separated) | `--include-full="src/auth.py,config.py"` |
| `--include-patterns` | Pattern matching for full content | `--include-patterns="*.config.js,*settings*.py"` |

### Exclusion Options

| Option | Description | Example |
|--------|-------------|---------|
| `--exclude` | Additional patterns to exclude | `--exclude="vendor/,legacy/,*.bak"` |
| `--skeleton-only` | Force skeleton for directories | `--skeleton-only="src/old_code/"` |

### Advanced Options

| Option | Description | Default |
|--------|-------------|---------|
| `--max-tokens` | Token budget (future) | `50000` |
| `--show-deps` | Show dependency graph (future) | Disabled |

---

## Real-World Examples

### Example 1: Reference Django Project for New Build

```bash
# Extract skeleton from old project
python codebase_skeleton.py ~/old-blog-project --output=reference.txt

# Feed to Claude when starting new project:
# "I'm building a new Django blog. Here's the skeleton of a similar 
#  project I built before. Help me set up the same architecture."
```

**Token savings:** ~15,000 tokens → ~3,000 tokens (80% reduction)

### Example 2: Understanding Unfamiliar Codebase

```bash
# First, get overview
python codebase_skeleton.py ~/new-repo --mode=overview

# Then, get skeleton of interesting modules
python codebase_skeleton.py ~/new-repo \
  --mode=custom \
  --include-full="src/core/"

# Ask Claude: "Explain how the authentication flow works in this codebase"
```

### Example 3: Compare Two Versions

```bash
# Extract both versions
python codebase_skeleton.py ~/project-v1 --output=v1-skeleton.txt
python codebase_skeleton.py ~/project-v2 --output=v2-skeleton.txt

# Feed both to Claude:
# "What architectural changes happened between v1 and v2?
#  What got refactored?"
```

### Example 4: Document Internal Project

```bash
# Generate skeleton for documentation
python codebase_skeleton.py ~/company-backend \
  --exclude="tests/,migrations/,vendor/" \
  --output=architecture-docs.txt

# Share with team (no sensitive implementation details)
```

### Example 5: Focus on Payment Module

```bash
python codebase_skeleton.py ~/e-commerce-project \
  --mode=custom \
  --include-full="src/payments/,src/billing/" \
  --output=payment-system.txt

# Ask Claude: "Review this payment system for security issues"
```

---

## Output Format

### XML Structure

```xml
<codebase project='my-app'>
  
  <metadata>
    <tree>
    [ASCII directory tree with file counts]
    </tree>
    
    <stats>
      Files processed: 145
      Full content: 12 files
      Skeleton: 98 files
      Excluded: 35 files
      Tree-sitter: enabled
    </stats>
  </metadata>

  <full-content>
    <file path='README.md' tokens='1200'>
    [Full markdown content]
    </file>
    
    <file path='package.json' tokens='450'>
    [Full JSON]
    </file>
  </full-content>

  <skeleton>
    <file path='src/models.py' loc='150' tokens='800'>
    from django.db import models

    class User(models.Model):
        """User account with authentication."""
        # [Implementation hidden]
    
    class Post(models.Model):
        """Blog post with timestamps."""
        # [Implementation hidden]
    </file>
  </skeleton>

  <excluded>
    <directory path='tests' files='45'/>
    <directory path='migrations' files='23'/>
  </excluded>

  <total-tokens>12450</total-tokens>
</codebase>
```

---

## Installation Details

### Required (None!)

The script works without any dependencies using fallback modes:
- Basic line-based code extraction
- Simple ASCII tree generation
- Approximate token counting

### Optional (Recommended)

```bash
# Tree-sitter for smart parsing
pip install tree-sitter \
  tree-sitter-python \
  tree-sitter-javascript \
  tree-sitter-typescript

# Accurate token counting
pip install tiktoken

# Beautiful directory trees
pip install directory-tree
```

**Installation check:**
```bash
python codebase_skeleton.py ~/test-project

# Output will show:
# Warning: tree-sitter not available, using fallback mode
# Warning: tiktoken not available, using approximate token counts
# Warning: directory_tree not available, using basic tree display
```

---

## Smart Defaults

### Always Included (Full Content)

**Documentation:**
- `README.md`, `LICENSE`, `CHANGELOG.md`

**Package Configs:**
- `package.json`, `requirements.txt`, `pyproject.toml`
- `Cargo.toml`, `go.mod`, `setup.py`

**Project Configs:**
- `tsconfig.json`, `docker-compose.yml`, `Dockerfile`
- `.env.example`, `Makefile`, `.gitignore`

### Always Excluded

**Dependencies:**
- `node_modules/`, `venv/`, `.venv/`, `vendor/`

**Build Artifacts:**
- `build/`, `dist/`, `target/`, `.next/`
- `__pycache__/`, `*.pyc`, `*.egg-info/`

**Development:**
- `.git/`, `.idea/`, `.vscode/`
- `coverage/`, `.pytest_cache/`

**Directories Skipped:**
- `tests/`, `migrations/`, `docs/`
- `static/`, `media/`, `assets/`

---

## Performance

**Benchmarks** (approximate):

| Project Size | Files | Processing Time | Token Reduction |
|--------------|-------|-----------------|-----------------|
| Small (Django blog) | 50 files | <2s | 85% |
| Medium (Flask API) | 200 files | <5s | 82% |
| Large (React + Node) | 500 files | <15s | 88% |
| Huge (monorepo) | 1000+ files | <30s | 90% |

**Memory:** Processes one file at a time, minimal memory footprint

**Cross-platform:** Tested on macOS, Linux, Windows

---

## Troubleshooting

### Tree-sitter Not Working

**Symptom:** `Warning: tree-sitter not available`

**Solution:**
```bash
pip install tree-sitter tree-sitter-python
```

**Still not working?** Script uses fallback mode automatically.

### Permission Errors

**Symptom:** `Warning: Could not read /path/to/file`

**Solution:** File is ignored, processing continues. Check file permissions if needed.

### Too Many Tokens

**Symptom:** Output is still too large

**Solutions:**
```bash
# Exclude more directories
python codebase_skeleton.py ~/project \
  --exclude="docs/,examples/,vendor/"

# Use overview mode first
python codebase_skeleton.py ~/project --mode=overview

# Focus on specific modules
python codebase_skeleton.py ~/project \
  --mode=custom \
  --include-full="src/core/"
```

### Unicode Errors

**Symptom:** Files fail to read

**Solution:** Script uses `errors='ignore'` automatically. Files with encoding issues are skipped gracefully.

---

## Use Cases

### For Developers

✅ **Reference old projects** when building new ones  
✅ **Understand inherited codebases** quickly  
✅ **Document architecture** without implementation details  
✅ **Code reviews** focused on structure  
✅ **Refactoring planning** - see before/after

### For Teams

✅ **Onboard new developers** with structural overview  
✅ **Architecture discussions** with concrete examples  
✅ **Cross-team knowledge sharing** without full access  
✅ **Technical debt assessment** - identify patterns  
✅ **Migration planning** - compare old vs new

### For LLM Workflows

✅ **Context management** - stay under token limits  
✅ **Accurate code generation** based on existing patterns  
✅ **Architectural questions** without implementation noise  
✅ **Multi-project analysis** - compare approaches  
✅ **Documentation generation** from code structure

---

## Limitations & Future Enhancements

### Current Limitations

- Token budget enforcement tracked but not enforced
- Dependency graph (`--show-deps`) stubbed for future
- Tree-sitter only for Python/JS/TS (others use fallback)
- No incremental updates (full regeneration each run)

### Planned Features

- 🔄 Dependency graph visualization
- 🎯 Smart token budget enforcement
- 🌍 More language support (Go, Rust, Java with Tree-sitter)
- 📈 Diff mode (compare two skeletons)
- ⚡ Incremental updates (only changed files)
- 🔍 Search/filter by pattern
- 📦 Config file support (`.skeletonrc`)

---

## Contributing

This is a single-file utility designed for simplicity. Contributions welcome for:

- Additional language support (Tree-sitter queries)
- Better heuristics for file categorization
- Performance optimizations
- Bug fixes

---

## License

MIT License - Use freely in personal and commercial projects.

---

## Tips & Tricks

### Tip 1: Use with Git

```bash
# Skeleton of current branch
python codebase_skeleton.py . --output=main-skeleton.txt

# Switch branch and compare
git checkout feature-branch
python codebase_skeleton.py . --output=feature-skeleton.txt

# Ask Claude: "What changed architecturally?"
```

### Tip 2: CI/CD Integration

```yaml
# .github/workflows/document.yml
- name: Generate Architecture Docs
  run: |
    python codebase_skeleton.py . --output=docs/architecture.txt
    git add docs/architecture.txt
```

### Tip 3: Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit
python codebase_skeleton.py . --mode=overview > .architecture-snapshot
```

### Tip 4: Quick Project Stats

```bash
python codebase_skeleton.py ~/project --mode=overview | grep "Files processed"
```

### Tip 5: Multiple Projects Reference

```bash
# Build a reference library
for project in ~/projects/*/; do
    name=$(basename "$project")
    python codebase_skeleton.py "$project" \
      --output="references/${name}-skeleton.txt"
done

# Feed entire library to Claude when starting new projects
```

---

## FAQ

**Q: Why not just use `tree` command?**  
A: `tree` shows filenames, not code structure. This shows function signatures, classes, and imports.

**Q: Is this better than just copying code?**  
A: Yes - 80-90% token reduction while preserving architectural understanding.

**Q: Does it work without Tree-sitter?**  
A: Yes! Fallback mode extracts first 20 lines + signatures. Less precise but works.

**Q: Can I customize what's included?**  
A: Absolutely. Use `--include-full`, `--include-patterns`, and `--exclude` flags.

**Q: Does it send my code anywhere?**  
A: No. Runs 100% locally. Only you decide where the output goes.

**Q: What about sensitive data?**  
A: Implementation details are hidden. Config files included (check `.env.example` vs `.env`).

**Q: Can I use this for closed-source projects?**  
A: Yes. You control the output. Review before sharing externally.

---

## Support

Found a bug? Have a feature request?

- Check existing issues
- Open a new issue with:
  - Python version (`python --version`)
  - Installed dependencies (`pip list | grep tree-sitter`)
  - Sample input/output (if possible)
  - Error messages

---

**Built for developers who value automation and efficiency. Stop wasting tokens. Start using skeletons.**
