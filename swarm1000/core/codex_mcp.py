"""Codex MCP integration for AI-powered code changes."""

import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List

from .logger import logger


class CodexMCP:
    """Integrates with Codex MCP server for AI-assisted code changes."""
    
    def __init__(self, mock_mode: bool = True):
        """
        Initialize Codex MCP integration.
        
        Args:
            mock_mode: If True, use mock mode instead of real Codex
        """
        self.mock_mode = mock_mode
        self.server_process = None
    
    def start_server(self, port: int = 8765) -> bool:
        """
        Start MCP server.
        
        Args:
            port: Port to run server on
            
        Returns:
            True if server started successfully
        """
        if self.mock_mode:
            logger.info("Codex MCP running in MOCK mode")
            return True
        
        try:
            # Try to start Codex MCP server
            # Example: npx -y codex mcp-server --port 8765
            self.server_process = subprocess.Popen(
                ["npx", "-y", "codex", "mcp-server", "--port", str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"Started Codex MCP server on port {port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start Codex MCP server: {e}")
            logger.info("Falling back to mock mode")
            self.mock_mode = True
            return True
    
    def stop_server(self) -> None:
        """Stop MCP server."""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait(timeout=5)
            logger.info("Stopped Codex MCP server")
    
    def apply_change(
        self,
        workdir: Path,
        instruction: str,
        files_hint: Optional[List[str]] = None,
        approval_policy: str = "never",
        sandbox: str = "workspace-write"
    ) -> Dict[str, Any]:
        """
        Apply a code change using Codex MCP.
        
        Args:
            workdir: Working directory to apply changes
            instruction: Natural language instruction for the change
            files_hint: Optional list of files to focus on
            approval_policy: Approval policy (never, always, auto)
            sandbox: Sandbox mode (workspace-write, workspace-read, none)
            
        Returns:
            Result dictionary with status and details
        """
        if self.mock_mode:
            return self._mock_apply_change(workdir, instruction, files_hint)
        
        try:
            # Call MCP API (this would be actual HTTP/RPC call)
            # For now, mock it
            logger.warning("Real Codex MCP not implemented, using mock")
            return self._mock_apply_change(workdir, instruction, files_hint)
        
        except Exception as e:
            logger.error(f"Failed to apply change via Codex MCP: {e}")
            return {
                "success": False,
                "error": str(e),
                "files_changed": [],
            }
    
    def _mock_apply_change(
        self,
        workdir: Path,
        instruction: str,
        files_hint: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Mock implementation of apply_change.
        
        In real implementation, this would call Codex MCP server.
        For demo purposes, we create a placeholder file.
        """
        logger.info(f"[MOCK] Applying change in {workdir}")
        logger.info(f"[MOCK] Instruction: {instruction}")
        
        # Create a mock change log file
        mock_file = workdir / ".swarm_changes.log"
        
        try:
            with open(mock_file, 'a') as f:
                f.write(f"\n--- Change Request ---\n")
                f.write(f"Instruction: {instruction}\n")
                f.write(f"Files hint: {files_hint}\n")
                f.write(f"Status: MOCKED (no actual changes made)\n")
                f.write(f"---\n")
            
            return {
                "success": True,
                "mock": True,
                "files_changed": [str(mock_file)],
                "message": "Mock change applied (no actual code changes)",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "files_changed": [],
            }
    
    def validate_change(self, workdir: Path) -> Dict[str, Any]:
        """
        Validate changes made in workdir.
        
        Args:
            workdir: Directory with changes
            
        Returns:
            Validation result
        """
        # Check if there are any changes
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=workdir,
                capture_output=True,
                text=True,
                check=True
            )
            
            has_changes = bool(result.stdout.strip())
            
            return {
                "valid": True,
                "has_changes": has_changes,
                "files": result.stdout.strip().split('\n') if has_changes else [],
            }
        except subprocess.CalledProcessError as e:
            return {
                "valid": False,
                "error": str(e),
            }
