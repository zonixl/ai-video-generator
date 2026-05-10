"""Security guardrails for agent-generated HyperFrames files."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath, PureWindowsPath


class HyperframesSecurityError(ValueError):
    pass


ALLOWED_SUFFIXES = {".html", ".css", ".js", ".json", ".txt", ".svg", ".png", ".jpg", ".jpeg", ".webp"}
DENIED_NAMES = {".env", "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock"}
DENIED_PARTS = {".git", "node_modules", "__pycache__"}
MAX_FILE_BYTES = 512 * 1024
MAX_TOTAL_BYTES = 5 * 1024 * 1024
MAX_FILE_COUNT = 20

DENIED_CONTENT_PATTERNS = [
    r"\bfetch\s*\(",
    r"\bXMLHttpRequest\b",
    r"\bWebSocket\b",
    r"\bEventSource\b",
    r"\bnavigator\.sendBeacon\b",
    r"\beval\s*\(",
    r"\bnew\s+Function\s*\(",
    r"\bdocument\.cookie\b",
    r"\blocalStorage\b",
    r"\bsessionStorage\b",
    r"\bindexedDB\b",
    r"\bimport\s*\(",
    r"\brequire\s*\(",
    r"\bprocess\.",
    r"\bchild_process\b",
    r"\bfs\.",
    r"\bDeno\.",
]

DENIED_CSS_PATTERNS = [
    r"@import\s+url\s*\(",
    r"url\s*\(\s*['\"]?\s*https?://",
]


def validate_relative_path(path: str) -> str:
    if not path or "\x00" in path:
        raise HyperframesSecurityError("Invalid empty path")
    if "\\" in path:
        path = path.replace("\\", "/")

    posix = PurePosixPath(path)
    windows = PureWindowsPath(path)
    if posix.is_absolute() or windows.is_absolute() or windows.drive:
        raise HyperframesSecurityError(f"Absolute paths are not allowed: {path}")
    if any(part in {"", ".", ".."} for part in posix.parts):
        raise HyperframesSecurityError(f"Path traversal is not allowed: {path}")
    if any(part in DENIED_PARTS for part in posix.parts):
        raise HyperframesSecurityError(f"Denied path segment: {path}")
    if posix.name in DENIED_NAMES:
        raise HyperframesSecurityError(f"Denied filename: {path}")
    if posix.suffix.lower() not in ALLOWED_SUFFIXES:
        raise HyperframesSecurityError(f"File extension is not allowed: {path}")
    return posix.as_posix()


def resolve_in_workspace(workspace: Path, path: str) -> Path:
    safe_path = validate_relative_path(path)
    root = workspace.resolve()
    target = (root / safe_path).resolve()
    if root != target and root not in target.parents:
        raise HyperframesSecurityError(f"Path escapes workspace: {path}")
    return target


def validate_content(path: str, content: str) -> None:
    encoded_size = len(content.encode("utf-8"))
    if encoded_size > MAX_FILE_BYTES:
        raise HyperframesSecurityError(f"File too large: {path}")
    suffix = Path(path).suffix.lower()
    patterns = list(DENIED_CONTENT_PATTERNS)
    if suffix == ".css":
        patterns.extend(DENIED_CSS_PATTERNS)
    for pattern in patterns:
        if re.search(pattern, content, flags=re.IGNORECASE):
            raise HyperframesSecurityError(f"Denied content pattern in {path}: {pattern}")


def validate_file_batch(files: list[tuple[str, str]]) -> None:
    if len(files) > MAX_FILE_COUNT:
        raise HyperframesSecurityError(f"Too many files: {len(files)}")
    total = 0
    seen: set[str] = set()
    for path, content in files:
        safe_path = validate_relative_path(path)
        if safe_path in seen:
            raise HyperframesSecurityError(f"Duplicate file path: {safe_path}")
        seen.add(safe_path)
        validate_content(safe_path, content)
        total += len(content.encode("utf-8"))
    if total > MAX_TOTAL_BYTES:
        raise HyperframesSecurityError("Generated files exceed total size limit")
