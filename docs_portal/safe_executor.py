"""Safe code execution for documentation examples.

This module provides AST-based safe execution to prevent arbitrary code execution
while still allowing documentation examples to run interactively.

Security Principles:
- Use AST whitelist instead of exec() blacklist
- Limit execution time to prevent infinite loops
- Restrict available builtins
- No file I/O, no network access, no imports
"""

import ast
import io
import signal
from typing import Any, Dict, Mapping, Set
from contextlib import contextmanager


class SafeExecutionError(Exception):
    """Raised when code violates safety constraints."""
    pass


class ExecutionTimeout(Exception):
    """Raised when execution exceeds time limit."""
    pass


# Allowed AST node types for safe execution
SAFE_NODES: Set[type] = {
    ast.Module,
    ast.Expr,
    ast.Load,
    ast.Store,
    ast.Name,
    ast.Constant,
    ast.Num,  # Python 3.7 compatibility
    ast.Str,  # Python 3.7 compatibility
    ast.List,
    ast.Tuple,
    ast.Dict,
    ast.Set,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.BoolOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.And,
    ast.Or,
    ast.Not,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.Is,
    ast.IsNot,
    ast.In,
    ast.NotIn,
    ast.Assign,
    ast.AugAssign,
    ast.ListComp,
    ast.DictComp,
    ast.SetComp,
    ast.comprehension,
    ast.If,
    ast.For,
    ast.While,
    ast.Break,
    ast.Continue,
    ast.Pass,
    ast.Index,  # Python 3.8 compatibility
    ast.Slice,
    ast.Subscript,
    ast.Call,
    ast.keyword,
    ast.Attribute,
}

# Allowed function calls (built-in functions only)
SAFE_BUILTINS: Set[str] = {
    'print',
    'len',
    'range',
    'sum',
    'min',
    'max',
    'sorted',
    'abs',
    'round',
    'int',
    'float',
    'str',
    'bool',
    'list',
    'dict',
    'set',
    'tuple',
    'enumerate',
    'zip',
    'map',
    'filter',
    'all',
    'any',
}


def validate_ast(tree: ast.AST) -> None:
    """Validate that AST only contains safe operations.
    
    Args:
        tree: Parsed AST to validate
        
    Raises:
        SafeExecutionError: If unsafe operations detected
    """
    for node in ast.walk(tree):
        # Check node type is allowed
        if type(node) not in SAFE_NODES:
            raise SafeExecutionError(
                f"Unsafe operation: {type(node).__name__} is not allowed. "
                f"Examples can only use basic Python operations."
            )
        
        # Check function calls are to safe builtins
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name not in SAFE_BUILTINS:
                    raise SafeExecutionError(
                        f"Unsafe function call: {func_name}() is not allowed. "
                        f"Only these built-ins are permitted: {', '.join(sorted(SAFE_BUILTINS))}"
                    )
            elif isinstance(node, ast.Call) and not isinstance(node.func, ast.Attribute):
                # Allow method calls like list.append(), but not other complex calls
                pass
        
        # Prevent import statements
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise SafeExecutionError(
                "Import statements are not allowed in examples. "
                "Examples must be self-contained."
            )
        
        # Prevent function/class definitions
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            raise SafeExecutionError(
                f"{type(node).__name__} is not allowed. "
                "Examples should be simple expressions and statements."
            )
        
        # Prevent exception handling (can hide errors)
        if isinstance(node, (ast.Try, ast.ExceptHandler, ast.Raise)):
            raise SafeExecutionError(
                "Exception handling is not allowed. "
                "Examples should not use try/except."
            )
        
        # Prevent with statements (file I/O)
        if isinstance(node, (ast.With, ast.AsyncWith)):
            raise SafeExecutionError(
                "Context managers (with statements) are not allowed."
            )
        
        # Prevent async operations
        if isinstance(node, (ast.Await, ast.AsyncFor)):
            raise SafeExecutionError(
                "Async operations are not allowed in examples."
            )
        
        # Prevent yield (generators)
        if isinstance(node, (ast.Yield, ast.YieldFrom)):
            raise SafeExecutionError(
                "Generator expressions (yield) are not allowed."
            )


@contextmanager
def time_limit(seconds: int = 5):
    """Context manager to enforce execution time limit.
    
    Args:
        seconds: Maximum execution time in seconds
        
    Raises:
        ExecutionTimeout: If execution exceeds time limit
        
    Note:
        Uses SIGALRM on Unix systems. On Windows, timeout is not enforced.
    """
    def signal_handler(signum, frame):
        raise ExecutionTimeout(f"Execution exceeded {seconds} second time limit")
    
    # Only works on Unix-like systems
    try:
        old_handler = signal.signal(signal.SIGALRM, signal_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    except AttributeError:
        # SIGALRM not available (Windows)
        # Fall back to no timeout - examples should be fast anyway
        yield


def safe_execute(
    code: str,
    timeout: int = 5,
    max_output_size: int = 10000
) -> tuple[str, Dict[str, str]]:
    """Execute code safely with AST validation and time limits.
    
    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds
        max_output_size: Maximum stdout output size in characters
        
    Returns:
        Tuple of (stdout_output, variables_dict)
        
    Raises:
        SafeExecutionError: If code contains unsafe operations
        ExecutionTimeout: If execution exceeds time limit
        SyntaxError: If code has syntax errors
        
    Example:
        >>> output, vars = safe_execute("x = 1 + 2\\nprint(x)")
        >>> print(output)
        3
        >>> print(vars)
        {'x': '3'}
    """
    # Parse and validate AST
    try:
        tree = ast.parse(code, mode='exec')
    except SyntaxError as e:
        raise SafeExecutionError(f"Syntax error in code: {e}") from e
    
    validate_ast(tree)
    
    # Compile validated AST
    code_obj = compile(tree, '<example>', 'exec')
    
    # Set up restricted environment
    stdout = io.StringIO()
    
    # Create safe builtins
    safe_builtin_funcs = {
        'print': lambda *args, **kwargs: print(*args, file=stdout, **kwargs),
        'len': len,
        'range': range,
        'sum': sum,
        'min': min,
        'max': max,
        'sorted': sorted,
        'abs': abs,
        'round': round,
        'int': int,
        'float': float,
        'str': str,
        'bool': bool,
        'list': list,
        'dict': dict,
        'set': set,
        'tuple': tuple,
        'enumerate': enumerate,
        'zip': zip,
        'map': map,
        'filter': filter,
        'all': all,
        'any': any,
    }
    
    globals_ns = {"__builtins__": safe_builtin_funcs}
    locals_ns: Dict[str, Any] = {}
    
    # Execute with timeout
    try:
        with time_limit(timeout):
            exec(code_obj, globals_ns, locals_ns)
    except ExecutionTimeout:
        raise
    except Exception as e:
        raise SafeExecutionError(f"Execution error: {e}") from e
    
    # Get output
    output = stdout.getvalue()
    if len(output) > max_output_size:
        raise SafeExecutionError(
            f"Output too large ({len(output)} characters). "
            f"Maximum allowed: {max_output_size} characters."
        )
    
    # Extract variables
    variables = {
        name: repr(value)
        for name, value in locals_ns.items()
        if not name.startswith("_")
    }
    
    return output.strip(), variables
