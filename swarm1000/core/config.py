"""Configuration management for Swarm-1000."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SwarmConfig:
    """Configuration for the Swarm orchestrator."""
    
    # Repository settings
    repo_root: Path
    workspace_root: Path
    
    # Concurrency settings
    default_concurrency: int = 20
    max_concurrency: int = 100
    
    # Database settings
    state_db_path: Path = None
    
    # Inventory settings
    max_depth: int = 6
    max_file_size_mb: int = 5
    allowed_extensions: tuple = (
        '.md', '.txt', '.rst', '.py', '.js', '.ts', '.go', '.rs',
        '.java', '.c', '.cpp', '.h', '.hpp', '.toml', '.json', '.yaml', '.yml'
    )
    
    # Quality gate settings
    quality_gate_mode: str = "strict"  # strict, permissive, skip
    
    # MCP settings
    codex_mcp_enabled: bool = False
    codex_mcp_mock: bool = True
    
    def __post_init__(self):
        """Initialize derived paths."""
        if self.state_db_path is None:
            self.state_db_path = self.repo_root / "swarm1000" / "data" / "state.sqlite"
        
        # Ensure paths are Path objects
        self.repo_root = Path(self.repo_root)
        self.workspace_root = Path(self.workspace_root)
        self.state_db_path = Path(self.state_db_path)


def get_default_config() -> SwarmConfig:
    """Get default configuration based on current environment."""
    repo_root = Path(os.getcwd())
    
    # Try to find git root using git command first (faster)
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=repo_root
        )
        if result.returncode == 0:
            repo_root = Path(result.stdout.strip())
    except Exception:
        # Fallback to manual search with max depth
        current = repo_root
        max_depth = 10
        depth = 0
        while current != current.parent and depth < max_depth:
            if (current / ".git").exists():
                repo_root = current
                break
            current = current.parent
            depth += 1
    
    workspace_root = repo_root.parent / f"{repo_root.name}-swarm"
    
    return SwarmConfig(
        repo_root=repo_root,
        workspace_root=workspace_root,
    )
