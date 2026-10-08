"""Zero-dependency .env file parser and loader for CTF toolkit."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Union


def parse_dotenv_text(text: str) -> Dict[str, str]:
    """Parse string content of a .env file into key-value pairs."""
    env_vars: Dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue

        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()

        if not key:
            continue

        # Handle quoted values
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            # Quoted: preserve anything inside quotes
            val = val[1:-1]
        else:
            # Unquoted: strip inline comments after space
            if " #" in val:
                val = val.split(" #", 1)[0].strip()
            elif "\t#" in val:
                val = val.split("\t#", 1)[0].strip()
            val = val.strip("\"'")

        env_vars[key] = val
    return env_vars


def find_dotenv_files(
    start_dir: Optional[Union[str, Path]] = None,
    workspace: Optional[Union[str, Path]] = None,
) -> List[Path]:
    """Find applicable .env files in priority order (most specific first)."""
    candidates: List[Path] = []

    # 1. Workspace-specific .env
    if workspace:
        ws_env = Path(workspace).expanduser().resolve() / ".env"
        if ws_env.is_file() and ws_env not in candidates:
            candidates.append(ws_env)

    # 2. Current working directory .env
    cwd_dir = Path(start_dir).expanduser().resolve() if start_dir else Path.cwd()
    cwd_env = cwd_dir / ".env"
    if cwd_env.is_file() and cwd_env not in candidates:
        candidates.append(cwd_env)

    # 3. Traversal up to repo root (stop at .git)
    current = cwd_dir
    while current.parent != current:
        if (current / ".git").is_dir():
            repo_env = current / ".env"
            if repo_env.is_file() and repo_env not in candidates:
                candidates.append(repo_env)
            break
        current = current.parent

    # 4. Global fallback in ~/.config/ctf_toolkit/.env
    global_env = Path.home() / ".config" / "ctf_toolkit" / ".env"
    if global_env.is_file() and global_env not in candidates:
        candidates.append(global_env)

    return candidates


def load_dotenv(
    target_path: Optional[Union[str, Path]] = None,
    workspace: Optional[Union[str, Path]] = None,
    override: bool = False,
) -> Dict[str, str]:
    """Load variables from .env files into os.environ.
    
    If target_path is specified, loads that file only.
    Otherwise, loads files found in candidate paths without overriding existing environment variables.
    """
    loaded_all: Dict[str, str] = {}
    paths: List[Path] = []

    if target_path:
        p = Path(target_path).expanduser().resolve()
        if p.is_file():
            paths.append(p)
    else:
        paths = find_dotenv_files(workspace=workspace)

    # Process in reverse priority order so more specific files override less specific ones
    for p in reversed(paths):
        try:
            content = p.read_text(encoding="utf-8")
            parsed = parse_dotenv_text(content)
            loaded_all.update(parsed)
        except OSError:
            continue

    # Apply to os.environ
    for k, v in loaded_all.items():
        if override or k not in os.environ:
            os.environ[k] = v

    return loaded_all
