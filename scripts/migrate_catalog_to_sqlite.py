#!/usr/bin/env python3
"""
Migrate Iconics catalog + embeddings index into SQLite.

This creates a SQLite database that becomes the authoritative store for icon
metadata, tags, and the embeddings row index mapping.

Inputs (defaults are repo-root relative):
- icon-catalog.json
- embeddings/icon_index.json
- embeddings/metadata.json (optional, imported if present)

Output:
- iconics.sqlite3 (or provided --db)
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS icons (
  id TEXT PRIMARY KEY,
  semantic_name TEXT NOT NULL,
  category TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  filename TEXT,
  source_file TEXT,
  metaphor TEXT,
  emotional_valence REAL,
  abstraction_level INTEGER,
  style TEXT,
  enrichment_confidence REAL
);

CREATE TABLE IF NOT EXISTS icon_tags (
  icon_id TEXT NOT NULL,
  tag TEXT NOT NULL,
  PRIMARY KEY (icon_id, tag),
  FOREIGN KEY (icon_id) REFERENCES icons(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS icon_used_in (
  icon_id TEXT NOT NULL,
  used_in TEXT NOT NULL,
  PRIMARY KEY (icon_id, used_in),
  FOREIGN KEY (icon_id) REFERENCES icons(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS embeddings_index (
  icon_id TEXT PRIMARY KEY,
  row_index INTEGER NOT NULL,
  FOREIGN KEY (icon_id) REFERENCES icons(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS embeddings_metadata (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  model TEXT,
  dimension INTEGER,
  count INTEGER,
  dtype TEXT,
  pretrained TEXT,
  device TEXT,
  timestamp TEXT
);

CREATE INDEX IF NOT EXISTS idx_icons_category ON icons(category);
CREATE INDEX IF NOT EXISTS idx_icons_semantic_name ON icons(semantic_name);
CREATE INDEX IF NOT EXISTS idx_icon_tags_tag ON icon_tags(tag);
CREATE INDEX IF NOT EXISTS idx_icon_used_in_used_in ON icon_used_in(used_in);
"""


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _get_str(icon: Dict[str, Any], *keys: str) -> Optional[str]:
    for key in keys:
        value = icon.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def validate_catalog(repo: Path, catalog: Dict[str, Any]) -> Tuple[bool, List[str]]:
    issues: List[str] = []
    icons = catalog.get("icons", [])
    if not isinstance(icons, list):
        return False, ["Catalog 'icons' is not a list"]

    ids: List[str] = []
    for entry in icons:
        if not isinstance(entry, dict):
            issues.append("Catalog contains a non-object icon entry")
            continue
        icon_id = entry.get("id")
        if not isinstance(icon_id, str) or not icon_id:
            issues.append("Catalog contains an entry with missing/invalid 'id'")
            continue
        ids.append(icon_id)

        path = _get_str(entry, "filename", "sourceFile")
        if path is None:
            issues.append(f"Icon '{icon_id}' missing filename/sourceFile")
        else:
            if path.startswith("/"):
                issues.append(f"Icon '{icon_id}' has absolute path: {path}")
            else:
                full = repo / path
                if not full.exists():
                    issues.append(f"Icon '{icon_id}' points to missing file: {path}")

    counts = Counter(ids)
    dupes = [icon_id for icon_id, count in counts.items() if count > 1]
    if dupes:
        issues.append(f"Duplicate icon IDs detected (examples): {sorted(dupes)[:5]}")

    return len(issues) == 0, issues


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def migrate(
    repo: Path,
    catalog_path: Path,
    embeddings_index_path: Path,
    embeddings_metadata_path: Optional[Path],
    db_path: Path,
    overwrite: bool,
) -> None:
    if db_path.exists():
        if not overwrite:
            raise SystemExit(f"Refusing to overwrite existing DB: {db_path} (use --overwrite)")
        db_path.unlink()

    catalog = load_json(catalog_path)
    ok, issues = validate_catalog(repo, catalog)
    if not ok:
        print("Catalog validation failed:")
        for issue in issues[:50]:
            print(f"  - {issue}")
        if len(issues) > 50:
            print(f"  - ... and {len(issues) - 50} more")
        raise SystemExit(2)

    embeddings_index = load_json(embeddings_index_path)
    if not isinstance(embeddings_index, dict):
        raise SystemExit("embeddings/icon_index.json must be an object mapping icon_id -> row_index")

    conn = connect(db_path)
    with conn:
        conn.executescript(SCHEMA_SQL)

        icons: Iterable[Dict[str, Any]] = catalog.get("icons", [])
        icon_insert = """
            INSERT INTO icons (
              id, semantic_name, category, description, filename, source_file,
              metaphor, emotional_valence, abstraction_level, style, enrichment_confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        tag_insert = "INSERT OR IGNORE INTO icon_tags (icon_id, tag) VALUES (?, ?)"
        used_in_insert = "INSERT OR IGNORE INTO icon_used_in (icon_id, used_in) VALUES (?, ?)"
        embed_insert = "INSERT OR REPLACE INTO embeddings_index (icon_id, row_index) VALUES (?, ?)"

        for icon in icons:
            icon_id = _get_str(icon, "id")
            if icon_id is None:
                continue

            semantic_name = _get_str(icon, "semanticName", "semantic_name") or icon_id
            category = _get_str(icon, "category") or "unknown"
            description = _get_str(icon, "description") or ""
            filename = _get_str(icon, "filename")
            source_file = _get_str(icon, "sourceFile")

            metaphor = _get_str(icon, "metaphor") or ""
            emotional_valence = icon.get("emotional_valence")
            abstraction_level = icon.get("abstraction_level")
            style = _get_str(icon, "style") or ""
            enrichment_confidence = icon.get("enrichment_confidence")

            conn.execute(
                icon_insert,
                (
                    icon_id,
                    semantic_name,
                    category,
                    description,
                    filename,
                    source_file,
                    metaphor if metaphor else None,
                    float(emotional_valence) if emotional_valence is not None else None,
                    int(abstraction_level) if abstraction_level is not None else None,
                    style if style else None,
                    float(enrichment_confidence) if enrichment_confidence is not None else None,
                ),
            )

            tags = icon.get("tags") or []
            if isinstance(tags, list):
                for tag in tags:
                    if isinstance(tag, str) and tag.strip():
                        conn.execute(tag_insert, (icon_id, tag.strip()))

            used_in = icon.get("usedIn") or icon.get("used_in") or []
            if isinstance(used_in, list):
                for value in used_in:
                    if isinstance(value, str) and value.strip():
                        conn.execute(used_in_insert, (icon_id, value.strip()))

            if icon_id in embeddings_index:
                conn.execute(embed_insert, (icon_id, int(embeddings_index[icon_id])))

        if embeddings_metadata_path and embeddings_metadata_path.exists():
            meta = load_json(embeddings_metadata_path)
            conn.execute("DELETE FROM embeddings_metadata WHERE id = 1")
            conn.execute(
                """
                INSERT INTO embeddings_metadata (
                  id, model, dimension, count, dtype, pretrained, device, timestamp
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    meta.get("model"),
                    meta.get("dimension"),
                    meta.get("count"),
                    meta.get("dtype"),
                    meta.get("pretrained"),
                    meta.get("device"),
                    meta.get("timestamp"),
                ),
            )

    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate Iconics catalog to SQLite")
    parser.add_argument("--db", type=Path, default=None, help="Output SQLite DB path")
    parser.add_argument("--catalog", type=Path, default=None, help="Path to icon-catalog.json")
    parser.add_argument("--embeddings-index", type=Path, default=None, help="Path to embeddings/icon_index.json")
    parser.add_argument(
        "--embeddings-metadata", type=Path, default=None, help="Path to embeddings/metadata.json"
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing DB")

    args = parser.parse_args()

    repo = repo_root()
    db_path = args.db or (repo / "iconics.sqlite3")
    catalog_path = args.catalog or (repo / "icon-catalog.json")
    embeddings_index_path = args.embeddings_index or (repo / "embeddings" / "icon_index.json")
    embeddings_metadata_path = args.embeddings_metadata or (repo / "embeddings" / "metadata.json")

    migrate(
        repo=repo,
        catalog_path=catalog_path,
        embeddings_index_path=embeddings_index_path,
        embeddings_metadata_path=embeddings_metadata_path,
        db_path=db_path,
        overwrite=args.overwrite,
    )

    print(f"SQLite catalog created: {db_path}")


if __name__ == "__main__":
    main()

