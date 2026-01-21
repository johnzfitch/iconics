"""
Iconics Vision Relabel Utilities

This module exists to fix large-scale taxonomy drift (e.g. too many 'ui' icons)
by re-running the vision labeler over existing icons and updating the catalog.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass
class RelabelStats:
    processed: int = 0
    updated: int = 0
    skipped_missing_file: int = 0
    skipped_no_path: int = 0
    errors: int = 0


def iter_icons_for_relabel(catalog: Dict, where_category: str) -> Iterable[Dict]:
    for icon in catalog.get("icons", []):
        if not isinstance(icon, dict):
            continue
        if icon.get("category") != where_category:
            continue
        yield icon


def resolve_icon_path(repo_root: Path, icon: Dict) -> Optional[Path]:
    path = icon.get("sourceFile") or icon.get("filename")
    if not isinstance(path, str) or not path.strip():
        return None
    p = Path(path)
    if p.is_absolute():
        return p
    return repo_root / p


def apply_label_to_icon(icon: Dict, label: Dict, update_fields: List[str]) -> Dict:
    updated = dict(icon)
    if "category" in update_fields and label.get("category"):
        updated["category"] = label["category"]
    if "tags" in update_fields and label.get("tags"):
        updated["tags"] = label["tags"]
    if "description" in update_fields and label.get("description") is not None:
        updated["description"] = label["description"]
    if "enrichment_confidence" in update_fields and label.get("confidence") is not None:
        try:
            updated["enrichment_confidence"] = float(label["confidence"])
        except Exception:
            pass
    return updated

