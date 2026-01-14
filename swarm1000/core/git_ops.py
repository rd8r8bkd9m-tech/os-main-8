"""Git operations for worktree management."""

import subprocess
from pathlib import Path

from .logger import logger


class GitOps:
    """Manages git operations for swarm workers."""

    def __init__(self, repo_root: Path, workspace_root: Path):
        """
        Initialize git operations manager.
        
        Args:
            repo_root: Root of the main repository
            workspace_root: Root directory for worker worktrees
        """
        self.repo_root = Path(repo_root)
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def create_worktree(self, worker_id: str, branch_name: str | None = None) -> Path:
        """
        Create a git worktree for a worker.
        
        Args:
            worker_id: Worker identifier (e.g., "worker-01")
            branch_name: Optional branch name (defaults to worker_id)
            
        Returns:
            Path to created worktree
        """
        if branch_name is None:
            branch_name = f"swarm/{worker_id}"

        worktree_path = self.workspace_root / "workers" / worker_id

        # Check if worktree already exists
        if worktree_path.exists():
            logger.info(f"Worktree already exists: {worktree_path}")
            return worktree_path

        worktree_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Create worktree
            subprocess.run(
                ["git", "worktree", "add", "-b", branch_name, str(worktree_path)],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Created worktree: {worktree_path} (branch: {branch_name})")
            return worktree_path
        except subprocess.CalledProcessError:
            # Branch might already exist, try without -b
            try:
                subprocess.run(
                    ["git", "worktree", "add", str(worktree_path), branch_name],
                    cwd=self.repo_root,
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.info(f"Created worktree from existing branch: {worktree_path}")
                return worktree_path
            except subprocess.CalledProcessError as e2:
                logger.error(f"Failed to create worktree: {e2.stderr}")
                raise

    def remove_worktree(self, worker_id: str) -> None:
        """
        Remove a git worktree.
        
        Args:
            worker_id: Worker identifier
        """
        worktree_path = self.workspace_root / "workers" / worker_id

        if not worktree_path.exists():
            logger.warning(f"Worktree does not exist: {worktree_path}")
            return

        try:
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_path), "--force"],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Removed worktree: {worktree_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to remove worktree: {e.stderr}")
            raise

    def commit_changes(
        self,
        worktree_path: Path,
        message: str,
        author: str | None = None
    ) -> str | None:
        """
        Commit changes in a worktree.
        
        Args:
            worktree_path: Path to worktree
            message: Commit message
            author: Optional author string (e.g., "Name <email>")
            
        Returns:
            Commit SHA if successful, None otherwise
        """
        try:
            # Stage all changes
            subprocess.run(
                ["git", "add", "."],
                cwd=worktree_path,
                check=True,
                capture_output=True
            )

            # Commit
            cmd = ["git", "commit", "-m", message]
            if author:
                cmd.extend(["--author", author])

            subprocess.run(
                cmd,
                cwd=worktree_path,
                check=True,
                capture_output=True,
                text=True
            )

            # Get commit SHA
            sha_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=worktree_path,
                check=True,
                capture_output=True,
                text=True
            )
            commit_sha = sha_result.stdout.strip()

            logger.info(f"Committed changes: {commit_sha[:8]} - {message}")
            return commit_sha
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit changes: {e.stderr}")
            return None

    def get_current_branch(self, worktree_path: Path) -> str | None:
        """Get current branch name in worktree."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=worktree_path,
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def has_changes(self, worktree_path: Path) -> bool:
        """Check if worktree has uncommitted changes."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=worktree_path,
                check=True,
                capture_output=True,
                text=True
            )
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            return False

    def list_worktrees(self) -> list[dict]:
        """List all worktrees."""
        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
                text=True
            )

            worktrees = []
            current = {}
            for line in result.stdout.split('\n'):
                if line.startswith('worktree '):
                    if current:
                        worktrees.append(current)
                    current = {'path': line.split(' ', 1)[1]}
                elif line.startswith('branch '):
                    current['branch'] = line.split(' ', 1)[1]
                elif line.startswith('HEAD '):
                    current['head'] = line.split(' ', 1)[1]

            if current:
                worktrees.append(current)

            return worktrees
        except subprocess.CalledProcessError:
            return []
