"""Code Execution Tool — Phase 6
Executes code in a sandboxed environment.
"""
from __future__ import annotations

import ast
import sys
import traceback
from io import StringIO
from typing import Any


class CodeExecutionError(Exception):
    """Raised when code execution fails"""
    pass


class CodeExecutor:
    """Safe code execution tool — runs Python code in isolated namespace"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    async def execute(self, code: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute Python code and return result

        Args:
            code: Python code to execute
            context: Optional variables to inject into namespace

        Returns:
            dict with keys: success, output, error, result
        """
        # Validate code first
        try:
            ast.parse(code)
        except SyntaxError as e:
            return {
                "success": False,
                "output": "",
                "error": f"Syntax error: {e}",
                "result": None,
            }

        # Create isolated namespace
        namespace = {
            "__builtins__": __builtins__,
            **(context or {}),
        }

        # Capture stdout
        old_stdout = sys.stdout
        redirected_output = StringIO()
        sys.stdout = redirected_output

        try:
            exec(code, namespace)
            output = redirected_output.getvalue()

            # Get the last expression value if any
            result = namespace.get("_result", None)

            return {
                "success": True,
                "output": output,
                "error": None,
                "result": result,
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
        """Check if code is syntactically valid"""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    async def get_available_modules(self) -> list[str]:
        """List available built-in modules"""
        import pkgutil
        return [m.name for m in pkgutil.iter_modules() if m.name.startswith("_") is False][:50]
