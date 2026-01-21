"""
Iconics Catalog I/O

Provides a single loader that can read the Iconics catalog from either:
- JSON (`icon-catalog.json`)
- SQLite (`iconics.sqlite3`, created by scripts/migrate_catalog_to_sqlite.py)

Callers generally want a JSON-compatible dict:
  { "version": "...", "icons": [ { ... }, ... ] }

This lets existing code continue to operate while the storage backend migrates.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def is_sqlite_catalog(path: Path) -> bool:
    return path.suffix.lower() in {".sqlite3", ".sqlite", ".db"}


def resolve_default_catalog_path() -> Path:
    """
    Resolve the default catalog path for the repo.

    Priority:
      1) ICONICS_DB env var (if set)
      2) <repo>/iconics.sqlite3 (if exists)
      3) <repo>/icon-catalog.json
    """
    env_value = os.environ.get("ICONICS_DB")
    if env_value:
        candidate = Path(env_value).expanduser()
        if candidate.exists():
            return candidate

    repo = _repo_root()
    sqlite_path = repo / "iconics.sqlite3"
    if sqlite_path.exists():
        return sqlite_path
    return repo / "icon-catalog.json"


def ensure_repo_relative_path(path: Path, repo_root: Optional[Path] = None) -> str:
    """
    Convert an absolute path under the repo to a repo-relative POSIX path.

    This is the permanent fix for catalog corruption caused by accidentally
    persisting absolute paths like /tmp/... into the catalog.
    """
    repo = (repo_root or _repo_root()).resolve()
    p = Path(path)

    if p.is_absolute():
        resolved = p.resolve()
        try:
            rel = resolved.relative_to(repo)
        except Exception as e:
            raise ValueError(f"Refusing to store absolute path outside repo: {p}") from e
        return rel.as_posix()

    resolved = (repo / p).resolve()
    try:
        rel = resolved.relative_to(repo)
    except Exception as e:
        raise ValueError(f"Refusing to store path outside repo: {p}") from e
    return rel.as_posix()


def _split_joined_lines(value: str) -> List[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def load_catalog(path: Path) -> Dict[str, Any]:
    """
    Load the catalog from JSON or SQLite into a JSON-compatible dict.
    """
    path = Path(path)
    if is_sqlite_catalog(path):
        return load_catalog_sqlite(path)
    return json.loads(path.read_text(encoding="utf-8"))


def load_catalog_sqlite(db_path: Path) -> Dict[str, Any]:
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(db_path)

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        exists = cur.execute(
            "SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type='table' AND name='icons')"
        ).fetchone()
        if not exists or not exists[0]:
            raise RuntimeError(
                "SQLite DB does not contain expected 'icons' table "
                "(did you run scripts/migrate_catalog_to_sqlite.py?)"
            )

        rows = cur.execute(
            """
            SELECT
              i.id,
              i.semantic_name,
              i.category,
              i.description,
              i.filename,
              i.source_file,
              i.metaphor,
              i.emotional_valence,
              i.abstraction_level,
              COALESCE((SELECT group_concat(t.tag, char(10)) FROM icon_tags t WHERE t.icon_id = i.id), '') AS tags_joined,
              COALESCE((SELECT group_concat(u.used_in, char(10)) FROM icon_used_in u WHERE u.icon_id = i.id), '') AS used_in_joined
            FROM icons i
            ORDER BY i.semantic_name ASC
            """
        ).fetchall()

        icons: List[Dict[str, Any]] = []
        for (
            icon_id,
            semantic_name,
            category,
            description,
            filename,
            source_file,
            metaphor,
            emotional_valence,
            abstraction_level,
            tags_joined,
            used_in_joined,
        ) in rows:
            icons.append(
                {
                    "id": icon_id,
                    "semanticName": semantic_name or icon_id,
                    "category": category or "unknown",
                    "description": description or "",
                    "filename": filename,
                    "sourceFile": source_file,
                    "tags": _split_joined_lines(tags_joined or ""),
                    "usedIn": _split_joined_lines(used_in_joined or ""),
                    "metaphor": metaphor,
                    "emotional_valence": emotional_valence,
                    "abstraction_level": abstraction_level,
                }
            )

        return {"version": "sqlite", "icons": icons}
    finally:
        conn.close()


def upsert_icon_sqlite(db_path: Path, icon: Dict[str, Any]) -> None:
    """
    Insert/update a single icon entry into the SQLite catalog.

    Expects a JSON-style dict (id, semanticName, tags, usedIn, etc.).
    """
    db_path = Path(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        with conn:
            icon_id = icon.get("id")
            if not isinstance(icon_id, str) or not icon_id.strip():
                raise ValueError("Icon entry missing required 'id'")

            semantic_name = icon.get("semanticName") or icon_id
            category = icon.get("category") or "unknown"
            description = icon.get("description") or ""
            filename = icon.get("filename")
            source_file = icon.get("sourceFile")
            metaphor = icon.get("metaphor")
            emotional_valence = icon.get("emotional_valence")
            abstraction_level = icon.get("abstraction_level")
            style = icon.get("style")
            enrichment_confidence = icon.get("enrichment_confidence")

            conn.execute(
                """
                INSERT INTO icons (
                  id, semantic_name, category, description, filename, source_file,
                  metaphor, emotional_valence, abstraction_level, style, enrichment_confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  semantic_name=excluded.semantic_name,
                  category=excluded.category,
                  description=excluded.description,
                  filename=excluded.filename,
                  source_file=excluded.source_file,
                  metaphor=excluded.metaphor,
                  emotional_valence=excluded.emotional_valence,
                  abstraction_level=excluded.abstraction_level,
                  style=excluded.style,
                  enrichment_confidence=excluded.enrichment_confidence
                """,
                (
                    icon_id,
                    str(semantic_name),
                    str(category),
                    str(description),
                    filename,
                    source_file,
                    metaphor,
                    float(emotional_valence) if emotional_valence is not None else None,
                    int(abstraction_level) if abstraction_level is not None else None,
                    str(style) if style is not None and str(style).strip() else None,
                    float(enrichment_confidence) if enrichment_confidence is not None else None,
                ),
            )

            conn.execute("DELETE FROM icon_tags WHERE icon_id = ?", (icon_id,))
            tags = icon.get("tags") or []
            if isinstance(tags, list):
                for tag in tags:
                    if isinstance(tag, str) and tag.strip():
                        conn.execute(
                            "INSERT OR IGNORE INTO icon_tags (icon_id, tag) VALUES (?, ?)",
                            (icon_id, tag.strip()),
                        )

            conn.execute("DELETE FROM icon_used_in WHERE icon_id = ?", (icon_id,))
            used_in = icon.get("usedIn") or icon.get("used_in") or []
            if isinstance(used_in, list):
                for value in used_in:
                    if isinstance(value, str) and value.strip():
                        conn.execute(
                            "INSERT OR IGNORE INTO icon_used_in (icon_id, used_in) VALUES (?, ?)",
                            (icon_id, value.strip()),
                        )
    finally:
        conn.close()
