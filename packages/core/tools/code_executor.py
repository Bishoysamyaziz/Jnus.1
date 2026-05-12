"""Code Execution Tool — Secure Sandbox
Executes code in a sandboxed environment with strict security restrictions.
"""
from __future__ import annotations

import ast
import os
import sys
import traceback
from io import StringIO
from typing import Any

# ── القائمة السوداء للـ modules الخطرة ──────────────────────────────
BLOCKED_MODULES = {
    "os", "subprocess", "shutil", "socket", "ctypes",
    "multiprocessing", "threading", "signal", "sys",
    "importlib", "builtins", "inspect", "code", "codeop",
    "pty", "fcntl", "resource", "grp", "pwd", "spwd",
    "crypt", "curses", "termios", "tty",
}

BLOCKED_KEYWORDS = [
    "__import__", "eval(", "exec(", "compile(", "open(",
    "getattr(", "setattr(", "delattr(", "globals()", "locals()",
    "vars(", "dir(", "type(", "isinstance(", "issubclass(",
]


class CodeExecutionError(Exception):
    """Raised when code execution fails"""
    pass


class CodeExecutor:
    """Secure code execution tool — runs Python code in isolated namespace with sandbox"""

    def __init__(self, timeout: int = 30, max_memory_mb: int = 128):
        self.timeout = timeout
        self.max_memory_mb = max_memory_mb

    def _check_blocked(self, code: str) -> str | None:
        """Check if code contains blocked modules or keywords. Returns error message or None."""
        # Check for import of blocked modules
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] in BLOCKED_MODULES:
                            return f"⚠️ Module '{alias.name}' is blocked for security reasons"
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split(".")[0] in BLOCKED_MODULES:
                        return f"⚠️ Module '{node.module}' is blocked for security reasons"
        except SyntaxError:
            pass  # Will be caught later

        # Check for blocked keywords
        for kw in BLOCKED_KEYWORDS:
            if kw in code:
                return f"⚠️ '{kw}' is blocked for security reasons"

        return None

    async def execute(self, code: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute Python code in a secure sandbox

        Args:
            code: Python code to execute
            context: Optional variables to inject into namespace

        Returns:
            dict with keys: success, output, error, result
        """
        # 1. Check for blocked modules/keywords
        blocked_msg = self._check_blocked(code)
        if blocked_msg:
            return {
                "success": False,
                "output": "",
                "error": blocked_msg,
                "result": None,
            }

        # 2. Validate syntax
        try:
            ast.parse(code)
        except SyntaxError as e:
            return {
                "success": False,
                "output": "",
                "error": f"Syntax error: {e}",
                "result": None,
            }

        # 3. Create restricted builtins (safe subset)
        safe_builtins = {
            "abs": abs, "all": all, "any": any, "ascii": ascii,
            "bin": bin, "bool": bool, "bytearray": bytearray,
            "bytes": bytes, "chr": chr, "complex": complex,
            "dict": dict, "divmod": divmod, "enumerate": enumerate,
            "filter": filter, "float": float, "format": format,
            "frozenset": frozenset, "hash": hash, "hex": hex,
            "id": id, "int": int, "iter": iter, "len": len,
            "list": list, "map": map, "max": max, "min": min,
            "next": next, "object": object, "oct": oct,
            "ord": ord, "pow": pow, "print": print,
            "range": range, "repr": repr, "reversed": reversed,
            "round": round, "set": set, "slice": slice,
            "sorted": sorted, "str": str, "sum": sum,
            "tuple": tuple, "type": type, "zip": zip,
            "True": True, "False": False, "None": None,
            "Exception": Exception, "ValueError": ValueError,
            "TypeError": TypeError, "KeyError": KeyError,
            "IndexError": IndexError, "StopIteration": StopIteration,
            "RuntimeError": RuntimeError, "ZeroDivisionError": ZeroDivisionError,
            "ArithmeticError": ArithmeticError, "AttributeError": AttributeError,
            "ImportError": ImportError, "ModuleNotFoundError": ModuleNotFoundError,
            "NameError": NameError, "SyntaxError": SyntaxError,
            "UnboundLocalError": UnboundLocalError,
            "isinstance": isinstance, "issubclass": issubclass,
            "hasattr": hasattr, "getattr": getattr,
            "setattr": setattr, "delattr": delattr,
            "callable": callable, "staticmethod": staticmethod,
            "classmethod": classmethod, "property": property,
            "super": super, "help": lambda: None,  # Disable help
            "exit": lambda: None, "quit": lambda: None,
            "input": lambda prompt="": "",  # Disable input
            "open": lambda *a, **kw: (_ for _ in ()).throw(PermissionError("File access is disabled")),
        }

        # 4. Create isolated namespace
        namespace = {
            "__builtins__": safe_builtins,
            **(context or {}),
        }

        # 5. Capture stdout
        old_stdout = sys.stdout
        redirected_output = StringIO()
        sys.stdout = redirected_output

        try:
            # Execute with timeout via signal (Unix only)
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError(f"Code execution timed out after {self.timeout}s")

            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout)

            try:
                exec(code, namespace)
            finally:
                signal.alarm(0)  # Disable alarm

            output = redirected_output.getvalue()

            # Get the last expression value if any
            result = namespace.get("_result", None)

            return {
                "success": True,
                "output": output,
                "error": None,
                "result": result,
            }
        except TimeoutError as e:
            return {
                "success": False,
                "output": redirected_output.getvalue(),
                "error": f"⏱️ {str(e)}",
                "result": None,
            }
        except Exception as e:
            return {
                "success": False,
                "output": redirected_output.getvalue(),
                "error": f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}",
                "result": None,
            }
        finally:
            sys.stdout = old_stdout

    async def validate(self, code: str) -> bool:
        """Check if code is syntactically valid and doesn't use blocked modules"""
        try:
            ast.parse(code)
            return self._check_blocked(code) is None
        except SyntaxError:
            return False

    async def get_available_modules(self) -> list[str]:
        """List available safe built-in modules"""
        import pkgutil
        return [m.name for m in pkgutil.iter_modules()
                if not m.name.startswith("_")
                and m.name not in BLOCKED_MODULES][:50]
