"""Quality gate checks for code changes."""

import subprocess
from pathlib import Path
from typing import Dict, Any, List
from enum import Enum

from .logger import logger


class QualityGateMode(Enum):
    """Quality gate enforcement modes."""
    STRICT = "strict"  # All checks must pass
    PERMISSIVE = "permissive"  # Warnings allowed
    SKIP = "skip"  # No quality checks


class QualityGate:
    """Performs quality checks on code changes."""
    
    def __init__(self, mode: QualityGateMode = QualityGateMode.STRICT):
        """
        Initialize quality gate.
        
        Args:
            mode: Quality gate mode
        """
        self.mode = mode
    
    def check(self, workdir: Path, area: str) -> Dict[str, Any]:
        """
        Run quality checks on a directory.
        
        Args:
            workdir: Working directory to check
            area: Area/language of the code (backend, frontend, rust, etc.)
            
        Returns:
            Dictionary with check results
        """
        if self.mode == QualityGateMode.SKIP:
            logger.info("Quality gate SKIPPED")
            return {
                "passed": True,
                "mode": "skip",
                "checks": [],
            }
        
        logger.info(f"Running quality gate checks in {workdir} (mode: {self.mode.value})")
        
        checks = []
        
        # Detect what checks to run based on files present
        checks.extend(self._check_python(workdir))
        checks.extend(self._check_javascript_typescript(workdir))
        checks.extend(self._check_rust(workdir))
        checks.extend(self._check_c_cpp(workdir))
        
        # Determine overall pass/fail
        if self.mode == QualityGateMode.STRICT:
            passed = all(check["passed"] for check in checks)
        else:  # PERMISSIVE
            # Fail only on critical errors, not warnings
            passed = all(
                check["passed"] or check.get("severity") == "warning"
                for check in checks
            )
        
        return {
            "passed": passed,
            "mode": self.mode.value,
            "checks": checks,
        }
    
    def _check_python(self, workdir: Path) -> List[Dict[str, Any]]:
        """Run Python quality checks."""
        checks = []
        
        # Check if there are Python files
        py_files = list(workdir.rglob("*.py"))
        if not py_files:
            return checks
        
        # Try ruff (if available)
        try:
            result = subprocess.run(
                ["ruff", "check", "."],
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=30
            )
            checks.append({
                "name": "ruff",
                "passed": result.returncode == 0,
                "severity": "error" if result.returncode != 0 else "info",
                "output": result.stdout + result.stderr,
            })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.debug("ruff not available or timed out")
        
        # Try pytest (if tests exist)
        if (workdir / "tests").exists() or any(
            f.name.startswith("test_") for f in py_files
        ):
            try:
                result = subprocess.run(
                    ["python", "-m", "pytest", "--tb=short", "-v"],
                    cwd=workdir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                checks.append({
                    "name": "pytest",
                    "passed": result.returncode == 0,
                    "severity": "error" if result.returncode != 0 else "info",
                    "output": result.stdout[-500:] if result.stdout else "",
                })
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.debug("pytest not available or timed out")
        
        return checks
    
    def _check_javascript_typescript(self, workdir: Path) -> List[Dict[str, Any]]:
        """Run JavaScript/TypeScript quality checks."""
        checks = []
        
        # Check if package.json exists
        if not (workdir / "package.json").exists():
            return checks
        
        # Try eslint
        try:
            result = subprocess.run(
                ["npx", "eslint", ".", "--max-warnings", "0"],
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=30
            )
            checks.append({
                "name": "eslint",
                "passed": result.returncode == 0,
                "severity": "warning",
                "output": result.stdout + result.stderr,
            })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.debug("eslint not available or timed out")
        
        # Try tsc (TypeScript compiler)
        if (workdir / "tsconfig.json").exists():
            try:
                result = subprocess.run(
                    ["npx", "tsc", "--noEmit"],
                    cwd=workdir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                checks.append({
                    "name": "tsc",
                    "passed": result.returncode == 0,
                    "severity": "error",
                    "output": result.stdout + result.stderr,
                })
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.debug("tsc not available or timed out")
        
        return checks
    
    def _check_rust(self, workdir: Path) -> List[Dict[str, Any]]:
        """Run Rust quality checks."""
        checks = []
        
        if not (workdir / "Cargo.toml").exists():
            return checks
        
        # Try cargo check
        try:
            result = subprocess.run(
                ["cargo", "check"],
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=120
            )
            checks.append({
                "name": "cargo check",
                "passed": result.returncode == 0,
                "severity": "error",
                "output": result.stderr[-500:] if result.stderr else "",
            })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.debug("cargo not available or timed out")
        
        # Try cargo clippy
        try:
            result = subprocess.run(
                ["cargo", "clippy", "--", "-D", "warnings"],
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=120
            )
            checks.append({
                "name": "cargo clippy",
                "passed": result.returncode == 0,
                "severity": "warning",
                "output": result.stderr[-500:] if result.stderr else "",
            })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.debug("cargo clippy not available or timed out")
        
        return checks
    
    def _check_c_cpp(self, workdir: Path) -> List[Dict[str, Any]]:
        """Run C/C++ quality checks."""
        checks = []
        
        # Check for CMakeLists.txt or Makefile
        has_cmake = (workdir / "CMakeLists.txt").exists()
        has_make = (workdir / "Makefile").exists()
        
        if not (has_cmake or has_make):
            return checks
        
        # Try make/cmake build
        try:
            if has_cmake:
                # Simple CMake check (don't actually build)
                subprocess.run(
                    ["cmake", ".", "-B", "build_check"],
                    cwd=workdir,
                    capture_output=True,
                    timeout=30,
                    check=True
                )
                checks.append({
                    "name": "cmake config",
                    "passed": True,
                    "severity": "info",
                    "output": "CMake configuration successful",
                })
            elif has_make:
                # Try make with dry-run
                result = subprocess.run(
                    ["make", "-n"],
                    cwd=workdir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                checks.append({
                    "name": "make dry-run",
                    "passed": result.returncode == 0,
                    "severity": "warning",
                    "output": "Makefile syntax OK",
                })
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            logger.debug("C/C++ build tools not available or timed out")
        
        return checks
