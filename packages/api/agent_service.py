"""OneAgent OS — Agent Service
Single powerful agent (Aider) for code generation, fixing, and explaining.
"""
from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Optional


class AgentService:
    """Wrapper around Aider for code tasks.

    Modes:
      - build: Generate new project from prompt
      - fix: Fix/refactor existing code
      - explain: Explain code
    """

    def __init__(self, timeout: int = 600):
        self.timeout = timeout

    async def run_task(
        self,
        prompt: str,
        mode: str = "build",
        repo_path: Optional[str] = None,
    ) -> dict[str, Any]:
        """Execute a task using Aider.

        Args:
            prompt: User prompt describing what to do
            mode: "build" | "fix" | "explain"
            repo_path: Path to existing repo (for fix/explain modes)

        Returns:
            dict with keys: success, output, files, logs, error
        """
        start_time = time.time()
        logs: list[str] = []
        workspace: Optional[str] = None

        try:
            logs.append(f"[agent] Starting task in mode={mode}")

            if mode == "build":
                workspace = tempfile.mkdtemp(prefix="oneagent_")
                logs.append(f"[agent] Created workspace: {workspace}")
                result = await self._build_project(prompt, workspace, logs)
            elif mode == "fix":
                if not repo_path:
                    raise ValueError("repo_path required for fix mode")
                result = await self._fix_code(prompt, repo_path, logs)
            elif mode == "explain":
                result = await self._explain_code(prompt, logs)
            else:
                raise ValueError(f"Unknown mode: {mode}")

            duration = time.time() - start_time
            logs.append(f"[agent] Task completed in {duration:.2f}s")

            return {
                "success": True,
                "output": result.get("output", ""),
                "files": result.get("files", []),
                "logs": logs,
                "duration": duration,
                "error": None,
            }

        except Exception as e:
            duration = time.time() - start_time
            logs.append(f"[agent] Task failed: {str(e)}")
            return {
                "success": False,
                "output": "",
                "files": [],
                "logs": logs,
                "duration": duration,
                "error": str(e),
            }
        finally:
            if workspace and os.path.exists(workspace):
                shutil.rmtree(workspace, ignore_errors=True)
                logs.append(f"[agent] Cleaned up workspace")

    async def _build_project(
        self, prompt: str, workspace: str, logs: list[str]
    ) -> dict[str, Any]:
        """Generate a new project using Aider."""
        logs.append("[agent] Building project with Aider...")

        # Detect project type from prompt
        project_type = self._detect_project_type(prompt)
        logs.append(f"[agent] Detected project type: {project_type}")

        # Create initial project structure based on type
        self._scaffold_project(workspace, project_type, logs)

        # Prepare Aider prompt with project context
        aider_prompt = f"""Create a complete {project_type} project at {workspace}.

Requirements:
{prompt}

Create all necessary files including:
- Source code files
- Configuration files (package.json, requirements.txt, etc.)
- README.md with setup instructions
- Any tests

Make it production-ready and working."""

        # Try to use Aider
        try:
            from aider.coders import Coder
            from aider.models import Model

            logs.append("[agent] Aider library found, using it...")
            llm_config = {
                "model": os.getenv("DEFAULT_MODEL", "deepseek-chat"),
                "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            }

            model = Model(llm_config["model"])
            coder = Coder.create(
                main_model=model,
                fnames=[workspace],
                auto_commits=False,
            )
            result = coder.run(aider_prompt)
            logs.append(f"[agent] Aider result: {str(result)[:200]}")

        except ImportError:
            logs.append("[agent] Aider library not available, using LLM direct...")
            # Fallback: use direct LLM call
            await self._llm_generate_project(workspace, prompt, project_type, logs)

        except Exception as e:
            logs.append(f"[agent] Aider failed: {str(e)}, using fallback...")
            await self._llm_generate_project(workspace, prompt, project_type, logs)

        # List generated files
        generated_files = []
        for root, dirs, files in os.walk(workspace):
            for f in files:
                if not f.startswith("."):
                    rel_path = os.path.relpath(os.path.join(root, f), workspace)
                    generated_files.append(rel_path)

        logs.append(f"[agent] Generated {len(generated_files)} files")

        # Get output summary
        readme_path = os.path.join(workspace, "README.md")
        output = f"Generated {len(generated_files)} files for {project_type} project.\n"
        if os.path.exists(readme_path):
            with open(readme_path) as f:
                output += f"\nREADME:\n{f.read()}"

        return {"output": output, "files": generated_files}

    async def _fix_code(self, prompt: str, repo_path: str, logs: list[str]) -> dict[str, Any]:
        """Fix or refactor existing code."""
        logs.append(f"[agent] Fixing code in {repo_path}...")

        try:
            from aider.coders import Coder
            from aider.models import Model

            llm_config = {
                "model": os.getenv("DEFAULT_MODEL", "deepseek-chat"),
                "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            }

            model = Model(llm_config["model"])
            coder = Coder.create(
                main_model=model,
                fnames=[repo_path],
                auto_commits=False,
            )
            result = coder.run(f"Fix/refactor: {prompt}")
            logs.append(f"[agent] Fix result: {str(result)[:200]}")

            return {"output": str(result), "files": [repo_path]}

        except ImportError:
            logs.append("[agent] Aider not available, returning instructions")
            return {
                "output": f"To fix this code:\n1. Install aider: pip install aider-chat\n2. Run: aider --model deepseek-chat --input '{prompt}'\n\nFor now, here's the analysis:\n{prompt}",
                "files": [repo_path],
            }

    async def _explain_code(self, prompt: str, logs: list[str]) -> dict[str, Any]:
        """Explain code or concepts."""
        logs.append("[agent] Explaining code...")

        # Use direct LLM call for explanations
        explanation = await self._llm_explain(prompt, logs)

        return {
            "output": explanation,
            "files": [],
        }

    async def _llm_generate_project(
        self, workspace: str, prompt: str, project_type: str, logs: list[str]
    ):
        """Generate project using direct LLM call."""
        logs.append("[agent] Using direct LLM for project generation...")

        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            logs.append("[agent] No API key available, creating template...")
            self._create_template_project(workspace, project_type, prompt)
            return

        llm_prompt = f"""Generate a complete {project_type} project.

Requirements: {prompt}

Create ALL files needed for a working project. Return ONLY valid JSON:
{{"files": [{{"path": "relative/file/path", "content": "file content here"}}]}}

Make each file complete and production-ready."""

        try:
            import httpx

            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": "You are a senior software engineer. Generate complete, working code."},
                            {"role": "user", "content": llm_prompt},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 8000,
                    },
                )

                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]

                    # Extract JSON from response
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]

                    try:
                        project_data = json.loads(content)
                        for file_info in project_data.get("files", []):
                            file_path = os.path.join(workspace, file_info["path"])
                            os.makedirs(os.path.dirname(file_path), exist_ok=True)
                            with open(file_path, "w") as f:
                                f.write(file_info["content"])
                        logs.append(f"[agent] Generated {len(project_data.get('files', []))} files via LLM")
                    except json.JSONDecodeError:
                        logs.append("[agent] Failed to parse LLM response as JSON")
                        self._create_template_project(workspace, project_type, prompt)
                else:
                    logs.append(f"[agent] LLM API error: {resp.status_code}")
                    self._create_template_project(workspace, project_type, prompt)

        except Exception as e:
            logs.append(f"[agent] LLM call failed: {str(e)}")
            self._create_template_project(workspace, project_type, prompt)

    async def _llm_explain(self, prompt: str, logs: list[str]) -> str:
        """Get explanation from LLM."""
        api_key = os.getenv("DEEPSEEK_API_KEY", "")

        if not api_key:
            return f"""## Explanation

Based on your request: **{prompt}**

To get a detailed AI-powered explanation:
1. Set DEEPSEEK_API_KEY in your .env file
2. Or use: aider --model deepseek-chat --input 'explain: {prompt}'

### Quick Analysis
Your request appears to be about code/concept explanation.
I'd recommend:
- Breaking down the problem into smaller parts
- Looking at documentation for specific technologies
- Using test-driven development to understand behavior"""

        try:
            import httpx

            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": "You are a senior software engineer. Explain code and concepts clearly."},
                            {"role": "user", "content": f"Explain this in detail with examples:\n\n{prompt}"},
                        ],
                        "temperature": 0.5,
                        "max_tokens": 2000,
                    },
                )

                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]

                return f"**Explanation for:** {prompt}\n\n(Unable to get AI explanation at this time. Please try again.)"

        except Exception as e:
            logs.append(f"[agent] LLM explanation failed: {str(e)}")
            return f"**Explanation for:** {prompt}\n\n*Error getting AI explanation. Please try again.*"

    def _detect_project_type(self, prompt: str) -> str:
        """Detect the type of project from the prompt."""
        prompt_lower = prompt.lower()

        if any(w in prompt_lower for w in ["landing page", "website", "site", "web page", "html", "css"]):
            return "landing-page"
        elif any(w in prompt_lower for w in ["api", "rest", "backend", "server", "fastapi", "express"]):
            return "api"
        elif any(w in prompt_lower for w in ["fullstack", "full-stack", "full stack", "react", "nextjs", "next.js"]):
            return "fullstack"
        elif any(w in prompt_lower for w in ["python", "script", "cli", "tool"]):
            return "python-tool"
        elif any(w in prompt_lower for w in ["bot", "discord", "telegram"]):
            return "bot"
        else:
            return "landing-page"

    def _scaffold_project(self, workspace: str, project_type: str, logs: list[str]):
        """Create initial project scaffolding."""
        logs.append(f"[agent] Scaffolding {project_type} project...")

        if project_type == "landing-page":
            self._scaffold_landing_page(workspace)
        elif project_type == "api":
            self._scaffold_api(workspace)
        elif project_type == "fullstack":
            self._scaffold_fullstack(workspace)
        elif project_type == "python-tool":
            self._scaffold_python_tool(workspace)
        else:
            self._scaffold_landing_page(workspace)

    def _scaffold_landing_page(self, workspace: str):
        """Scaffold a landing page project."""
        index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Landing Page</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <nav>
            <div class="logo">Logo</div>
            <ul>
                <li><a href="#features">Features</a></li>
                <li><a href="#about">About</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </nav>
        <div class="hero">
            <h1>Welcome to Your Project</h1>
            <p>Generated by OneAgent OS</p>
            <a href="#contact" class="cta-button">Get Started</a>
        </div>
    </header>
    <main>
        <section id="features">
            <h2>Features</h2>
            <div class="feature-grid">
                <div class="feature-card">
                    <h3>Feature 1</h3>
                    <p>Description of feature 1</p>
                </div>
                <div class="feature-card">
                    <h3>Feature 2</h3>
                    <p>Description of feature 2</p>
                </div>
                <div class="feature-card">
                    <h3>Feature 3</h3>
                    <p>Description of feature 3</p>
                </div>
            </div>
        </section>
    </main>
    <footer>
        <p>&copy; 2026 OneAgent OS. All rights reserved.</p>
    </footer>
    <script src="script.js"></script>
</body>
</html>"""

        styles_css = """* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
}

header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
}

nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
}

nav ul {
    display: flex;
    list-style: none;
    gap: 2rem;
}

nav a {
    color: white;
    text-decoration: none;
}

.hero {
    text-align: center;
    padding: 4rem 2rem;
    max-width: 800px;
    margin: 0 auto;
}

.hero h1 {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.cta-button {
    display: inline-block;
    padding: 1rem 2rem;
    background: white;
    color: #667eea;
    text-decoration: none;
    border-radius: 5px;
    margin-top: 2rem;
    font-weight: bold;
}

section {
    padding: 4rem 2rem;
    max-width: 1200px;
    margin: 0 auto;
}

.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
}

.feature-card {
    padding: 2rem;
    border: 1px solid #e1e1e1;
    border-radius: 8px;
    transition: transform 0.3s;
}

.feature-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

footer {
    background: #333;
    color: white;
    text-align: center;
    padding: 2rem;
}"""

        script_js = """// Main application script
document.addEventListener('DOMContentLoaded', () => {
    console.log('Landing page loaded!');
    
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});"""

        package = """{
  "name": "landing-page",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "npx serve .",
    "build": "echo 'Static site - no build needed'"
  }
}"""

        readme = f"""# Landing Page

Generated by OneAgent OS.

## Quick Start

1. Open `index.html` in your browser
2. Or run `npx serve .` for a local server

## Structure

- `index.html` - Main page
- `styles.css` - Styles
- `script.js` - JavaScript
"""

        os.makedirs(workspace, exist_ok=True)
        with open(os.path.join(workspace, "index.html"), "w") as f:
            f.write(index_html)
        with open(os.path.join(workspace, "styles.css"), "w") as f:
            f.write(styles_css)
        with open(os.path.join(workspace, "script.js"), "w") as f:
            f.write(script_js)
        with open(os.path.join(workspace, "package.json"), "w") as f:
            f.write(package)
        with open(os.path.join(workspace, "README.md"), "w") as f:
            f.write(readme)

    def _scaffold_api(self, workspace: str):
        """Scaffold a Python FastAPI project."""
        main_py = """from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="My API", version="1.0.0")

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

items_db = {}

@app.get("/")
async def root():
    return {"message": "API is running", "version": "1.0.0"}

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]

@app.post("/items")
async def create_item(item: Item):
    item_id = len(items_db) + 1
    items_db[item_id] = item
    return {"id": item_id, **item.model_dump()}

@app.get("/items")
async def list_items():
    return {"items": [{"id": k, **v.model_dump()} for k, v in items_db.items()]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

        requirements = """fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.9.2
"""

        readme = f"""# API Project

Generated by OneAgent OS.

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

## Endpoints

- GET / - Health check
- GET /items - List all items
- GET /items/{{id}} - Get item by ID
- POST /items - Create new item
"""

        os.makedirs(workspace, exist_ok=True)
        with open(os.path.join(workspace, "main.py"), "w") as f:
            f.write(main_py)
        with open(os.path.join(workspace, "requirements.txt"), "w") as f:
            f.write(requirements)
        with open(os.path.join(workspace, "README.md"), "w") as f:
            f.write(readme)

    def _scaffold_fullstack(self, workspace: str):
        """Scaffold a fullstack project."""
        self._scaffold_api(workspace)
        # Add frontend structure
        frontend_dir = os.path.join(workspace, "frontend")
        os.makedirs(frontend_dir, exist_ok=True)

        with open(os.path.join(frontend_dir, "index.html"), "w") as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fullstack App</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; }
        .container { display: flex; flex-direction: column; gap: 1rem; }
        input, button { padding: 0.5rem; font-size: 1rem; }
        #items { list-style: none; padding: 0; }
        #items li { padding: 0.5rem; border: 1px solid #ddd; margin: 0.5rem 0; border-radius: 4px; }
    </style>
</head>
<body>
    <h1>Fullstack App</h1>
    <div class="container">
        <div>
            <input type="text" id="itemName" placeholder="Item name">
            <input type="number" id="itemPrice" placeholder="Price">
            <button onclick="addItem()">Add Item</button>
        </div>
        <ul id="items"></ul>
    </div>
    <script>
        const API_URL = 'http://localhost:8000';
        
        async function loadItems() {
            const res = await fetch(`${API_URL}/items`);
            const data = await res.json();
            const list = document.getElementById('items');
            list.innerHTML = data.items.map(item => 
                `<li>${item.name} - $${item.price}</li>`
            ).join('');
        }

        async function addItem() {
            const name = document.getElementById('itemName').value;
            const price = parseFloat(document.getElementById('itemPrice').value);
            await fetch(`${API_URL}/items`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ name, price })
            });
            loadItems();
        }

        loadItems();
    </script>
</body>
</html>""")

    def _scaffold_python_tool(self, workspace: str):
        """Scaffold a Python CLI tool."""
        tool_py = """#!/usr/bin/env python3
\"\"\"CLI Tool - Generated by OneAgent OS\"\"\"
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="CLI Tool")
    parser.add_argument("input", help="Input argument")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"[VERBOSE] Processing: {args.input}")
    
    print(f"Hello, {args.input}!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""

        readme = f"""# Python CLI Tool

Generated by OneAgent OS.

## Usage

```bash
python cli.py "World"
python cli.py "World" --verbose
```
"""

        os.makedirs(workspace, exist_ok=True)
        with open(os.path.join(workspace, "cli.py"), "w") as f:
            f.write(tool_py)
        with open(os.path.join(workspace, "README.md"), "w") as f:
            f.write(readme)

    def _create_template_project(self, workspace: str, project_type: str, prompt: str):
        """Create a basic template when LLM is unavailable."""
        self._scaffold_project(workspace, project_type, [])
        # Update README with user's prompt context
        readme_path = os.path.join(workspace, "README.md")
        if os.path.exists(readme_path):
            with open(readme_path, "a") as f:
                f.write(f"\n## Original Request\n\n{prompt}\n")
