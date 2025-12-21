# Inventory Schema

## Overview

The inventory system scans directories to discover projects and collect metadata for planning.

## Output Format

The inventory is stored as JSON in `swarm1000/data/inventory.json`.

### Top-Level Structure

```json
{
  "version": "1.0",
  "total_projects": 42,
  "projects": [...]
}
```

### Project Item Schema

Each project in the `projects` array has the following structure:

```json
{
  "path": "/absolute/path/to/project",
  "name": "project-name",
  "languages": ["Python", "JavaScript", "Rust"],
  "build_systems": ["npm", "cargo", "python-pip"],
  "size_kb": 15420,
  "file_count": 523,
  "git_active": true,
  "git_commits_30d": 47,
  "readme_content": "# Project Title\n\nDescription...",
  "metadata": {
    "has_tests": true,
    "has_docs": true
  }
}
```

## Fields

### `path` (string, required)
Absolute filesystem path to the project root directory.

### `name` (string, required)
Base name of the project directory.

### `languages` (array of strings, required)
Programming languages detected by file extensions:
- Python (.py)
- JavaScript (.js)
- TypeScript (.ts, .tsx)
- Rust (.rs)
- Go (.go)
- Java (.java)
- C/C++ (.c, .cpp, .h, .hpp)
- And others...

### `build_systems` (array of strings, required)
Build/package management systems detected:
- `npm` - package.json found
- `cargo` - Cargo.toml found
- `go` - go.mod found
- `python-poetry` - pyproject.toml found
- `python-pip` - requirements.txt found
- `python-setuptools` - setup.py found
- `cmake` - CMakeLists.txt found
- `make` - Makefile found
- `gradle` - build.gradle found
- `maven` - pom.xml found
- `composer` - composer.json found

### `size_kb` (integer, required)
Total size of all files in the project (in kilobytes).

Note: Scanning may be limited for very large directories (>10,000 files).

### `file_count` (integer, required)
Total number of files in the project.

Note: Count may be approximate for very large directories.

### `git_active` (boolean, required)
Indicates if the project is a git repository (has .git directory).

### `git_commits_30d` (integer, required)
Number of git commits in the last 30 days.

Set to 0 if:
- Not a git repository
- Git command fails
- Repository has no commits

### `readme_content` (string or null, optional)
Content of the README file (if found).

README detection looks for (in order):
1. README.md
2. README.txt
3. README.rst
4. README

Constraints:
- Maximum 10KB of content (truncated if larger)
- Only text files (no binaries)
- UTF-8 encoding with error handling

### `metadata` (object, required)
Additional project metadata.

#### `metadata.has_tests` (boolean)
Indicates if project has test directory:
- `test/`
- `tests/`
- `spec/`
- `__tests__/`

#### `metadata.has_docs` (boolean)
Indicates if project has documentation directory:
- `docs/`
- `doc/`
- `documentation/`

## Scanning Configuration

### Default Settings

```python
max_depth = 6              # Maximum directory depth
max_file_size_mb = 5       # Maximum file size to read
```

### Excluded Directories

The scanner automatically skips:
- Hidden directories (starting with `.` except repository root)
- `node_modules`
- `__pycache__`
- `.git`
- `.venv`, `venv`
- `build`, `dist`, `target`
- `.cache`, `.pytest_cache`

### Project Detection

A directory is considered a project root if it contains:
- Any build system file (package.json, Cargo.toml, etc.), OR
- A .git directory, OR
- A README file

## Usage

### Command Line

```bash
python -m swarm1000.swarm inventory \
  --roots /path/to/projects /another/path \
  --max-depth 6 \
  --max-file-size 5
```

### Programmatic

```python
from swarm1000.core.inventory import InventoryScanner, save_inventory

scanner = InventoryScanner(max_depth=6, max_file_size_mb=5)
items = scanner.scan_roots(["/path/to/projects"])
save_inventory(items, Path("inventory.json"))
```

## Use Cases

The inventory is used for:

1. **Task Planning**
   - Understanding project landscape
   - Identifying technologies in use
   - Detecting active vs. dormant projects

2. **Resource Allocation**
   - Matching agent skills to project needs
   - Prioritizing active projects

3. **Documentation**
   - Extracting project descriptions from READMEs
   - Building knowledge base

4. **Dependency Analysis**
   - Understanding build tool requirements
   - Planning integration work

## Limitations

1. **Performance**
   - Large directories may have incomplete scans
   - File count limit: 10,000 files per project

2. **Language Detection**
   - Based on file extensions only
   - May miss languages in generated code
   - May detect build artifacts

3. **Git Activity**
   - Requires git command available
   - Only counts commits, not other activity
   - Private repos may require credentials

4. **README Content**
   - Limited to 10KB (may truncate large files)
   - Encoding issues may result in garbled text
   - Binary READMEs are skipped

## Best Practices

1. **Scope Appropriately**
   - Don't scan system directories
   - Focus on development workspace
   - Use max-depth to limit scope

2. **Review Results**
   - Check inventory.json before planning
   - Verify detected languages are accurate
   - Remove unwanted projects

3. **Update Regularly**
   - Re-run inventory when projects change
   - Track git activity trends
   - Monitor project growth

## Example Output

```json
{
  "version": "1.0",
  "total_projects": 3,
  "projects": [
    {
      "path": "/Users/dev/kolibri-backend",
      "name": "kolibri-backend",
      "languages": ["Python", "Shell"],
      "build_systems": ["python-pip"],
      "size_kb": 8450,
      "file_count": 342,
      "git_active": true,
      "git_commits_30d": 23,
      "readme_content": "# Kolibri Backend\n\nFastAPI backend service...",
      "metadata": {
        "has_tests": true,
        "has_docs": true
      }
    },
    {
      "path": "/Users/dev/kolibri-frontend",
      "name": "kolibri-frontend",
      "languages": ["TypeScript", "JavaScript", "CSS"],
      "build_systems": ["npm"],
      "size_kb": 45200,
      "file_count": 1523,
      "git_active": true,
      "git_commits_30d": 67,
      "readme_content": "# Kolibri Frontend\n\nReact/TypeScript SPA...",
      "metadata": {
        "has_tests": true,
        "has_docs": false
      }
    }
  ]
}
```
