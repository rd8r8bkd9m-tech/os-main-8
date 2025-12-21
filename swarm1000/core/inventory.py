"""Inventory scanning for directories and repositories."""

import json
import os
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from .logger import logger


@dataclass
class ProjectInventoryItem:
    """Represents a discovered project/directory."""
    path: str
    name: str
    languages: List[str]
    build_systems: List[str]
    size_kb: int
    file_count: int
    git_active: bool
    git_commits_30d: int
    readme_content: Optional[str]
    metadata: Dict[str, Any]


class InventoryScanner:
    """Scans directories to build an inventory of projects."""
    
    # Build system indicators
    BUILD_INDICATORS = {
        "package.json": "npm",
        "Cargo.toml": "cargo",
        "go.mod": "go",
        "pyproject.toml": "python-poetry",
        "requirements.txt": "python-pip",
        "setup.py": "python-setuptools",
        "CMakeLists.txt": "cmake",
        "Makefile": "make",
        "build.gradle": "gradle",
        "pom.xml": "maven",
        "composer.json": "composer",
    }
    
    # Language indicators by extension
    LANGUAGE_EXTENSIONS = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".jsx": "React",
        ".tsx": "React/TypeScript",
        ".go": "Go",
        ".rs": "Rust",
        ".java": "Java",
        ".c": "C",
        ".cpp": "C++",
        ".cc": "C++",
        ".h": "C/C++",
        ".hpp": "C++",
        ".cs": "C#",
        ".rb": "Ruby",
        ".php": "PHP",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".r": "R",
        ".m": "Objective-C",
        ".sh": "Shell",
    }
    
    def __init__(self, max_depth: int = 6, max_file_size_mb: int = 5,
                 allowed_extensions: tuple = None):
        """
        Initialize inventory scanner.
        
        Args:
            max_depth: Maximum directory depth to scan
            max_file_size_mb: Maximum file size to read (in MB)
            allowed_extensions: Tuple of allowed file extensions for reading
        """
        self.max_depth = max_depth
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.allowed_extensions = allowed_extensions or (
            '.md', '.txt', '.rst', '.py', '.js', '.ts', '.go', '.rs',
            '.java', '.c', '.cpp', '.h', '.hpp', '.toml', '.json',
            '.yaml', '.yml'
        )
    
    def scan_roots(self, root_paths: List[str]) -> List[ProjectInventoryItem]:
        """
        Scan multiple root directories.
        
        Args:
            root_paths: List of root directory paths to scan
            
        Returns:
            List of discovered project inventory items
        """
        all_items = []
        
        for root_path in root_paths:
            root = Path(root_path).expanduser().resolve()
            if not root.exists():
                logger.warning(f"Root path does not exist: {root}")
                continue
            
            logger.info(f"Scanning root: {root}")
            items = self._scan_directory(root, depth=0)
            all_items.extend(items)
        
        logger.info(f"Total projects discovered: {len(all_items)}")
        return all_items
    
    def _scan_directory(self, path: Path, depth: int) -> List[ProjectInventoryItem]:
        """Recursively scan a directory."""
        if depth > self.max_depth:
            return []
        
        items = []
        
        # Skip hidden directories and common ignore patterns
        if path.name.startswith('.') and path.name != '.':
            return []
        
        skip_dirs = {
            'node_modules', '__pycache__', '.git', '.venv', 'venv',
            'build', 'dist', 'target', '.cache', '.pytest_cache'
        }
        if path.name in skip_dirs:
            return []
        
        # Check if this is a project root
        if self._is_project_root(path):
            item = self._analyze_project(path)
            if item:
                items.append(item)
        
        # Recurse into subdirectories
        try:
            for child in path.iterdir():
                if child.is_dir():
                    items.extend(self._scan_directory(child, depth + 1))
        except PermissionError:
            logger.warning(f"Permission denied: {path}")
        
        return items
    
    def _is_project_root(self, path: Path) -> bool:
        """Check if directory is a project root."""
        # Has build system files
        for indicator in self.BUILD_INDICATORS.keys():
            if (path / indicator).exists():
                return True
        
        # Has .git directory
        if (path / ".git").exists():
            return True
        
        # Has README
        for readme in ["README.md", "README.txt", "README.rst", "README"]:
            if (path / readme).exists():
                return True
        
        return False
    
    def _analyze_project(self, path: Path) -> Optional[ProjectInventoryItem]:
        """Analyze a project directory."""
        try:
            # Detect build systems
            build_systems = []
            for indicator, system in self.BUILD_INDICATORS.items():
                if (path / indicator).exists():
                    build_systems.append(system)
            
            # Detect languages
            languages = self._detect_languages(path)
            
            # Calculate size
            size_kb, file_count = self._calculate_size(path)
            
            # Check git activity
            git_active = (path / ".git").exists()
            git_commits_30d = 0
            if git_active:
                git_commits_30d = self._count_recent_commits(path)
            
            # Read README
            readme_content = self._read_readme(path)
            
            # Additional metadata
            metadata = {
                "has_tests": self._has_tests(path),
                "has_docs": self._has_docs(path),
            }
            
            return ProjectInventoryItem(
                path=str(path),
                name=path.name,
                languages=languages,
                build_systems=build_systems,
                size_kb=size_kb,
                file_count=file_count,
                git_active=git_active,
                git_commits_30d=git_commits_30d,
                readme_content=readme_content,
                metadata=metadata,
            )
        except Exception as e:
            logger.error(f"Error analyzing project {path}: {e}")
            return None
    
    def _detect_languages(self, path: Path) -> List[str]:
        """Detect programming languages in directory."""
        languages: Set[str] = set()
        
        try:
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    if ext in self.LANGUAGE_EXTENSIONS:
                        languages.add(self.LANGUAGE_EXTENSIONS[ext])
                
                # Limit scanning
                if len(languages) > 20:
                    break
        except Exception:
            pass
        
        return sorted(list(languages))
    
    def _calculate_size(self, path: Path) -> tuple:
        """Calculate total size and file count."""
        total_size = 0
        file_count = 0
        
        try:
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
                
                # Limit scanning for large directories
                if file_count > 10000:
                    break
        except Exception:
            pass
        
        return total_size // 1024, file_count
    
    def _count_recent_commits(self, path: Path) -> int:
        """Count git commits in last 30 days."""
        try:
            result = subprocess.run(
                ["git", "-C", str(path), "log", "--since=30.days.ago", "--oneline"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return len(result.stdout.strip().split('\n'))
        except Exception:
            pass
        return 0
    
    def _read_readme(self, path: Path) -> Optional[str]:
        """Read README file if it exists."""
        for readme_name in ["README.md", "README.txt", "README.rst", "README"]:
            readme_path = path / readme_name
            if readme_path.exists():
                try:
                    size = readme_path.stat().st_size
                    if size > self.max_file_size_bytes:
                        logger.warning(f"README too large: {readme_path}")
                        continue
                    
                    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Limit to first 10KB
                        return content[:10240]
                except Exception as e:
                    logger.warning(f"Error reading README {readme_path}: {e}")
        return None
    
    def _has_tests(self, path: Path) -> bool:
        """Check if project has tests."""
        test_indicators = ["test", "tests", "spec", "__tests__"]
        for indicator in test_indicators:
            if (path / indicator).exists():
                return True
        return False
    
    def _has_docs(self, path: Path) -> bool:
        """Check if project has documentation."""
        doc_indicators = ["docs", "doc", "documentation"]
        for indicator in doc_indicators:
            if (path / indicator).exists():
                return True
        return False


def save_inventory(items: List[ProjectInventoryItem], output_path: Path) -> None:
    """Save inventory to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "version": "1.0",
        "total_projects": len(items),
        "projects": [asdict(item) for item in items]
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved inventory of {len(items)} projects to {output_path}")


def load_inventory(input_path: Path) -> List[ProjectInventoryItem]:
    """Load inventory from JSON file."""
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    items = [ProjectInventoryItem(**proj) for proj in data.get("projects", [])]
    logger.info(f"Loaded inventory of {len(items)} projects from {input_path}")
    return items
