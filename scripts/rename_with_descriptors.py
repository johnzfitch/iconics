#!/usr/bin/env python3
"""Add descriptive qualifiers to icon filenames.

Rules:
- Target only specific icon families (prefix before first dash)
- Append configured descriptors plus color/emotion/style hints if they are
  not already present in the slug
- Ensure filenames remain lowercase, dash-delimited, PNG files
"""

from __future__ import annotations

import re
from pathlib import Path

RAW_DIR = Path("/home/zack/dev/iconics/raw")
TARGET_PREFIXES = {
    "2000mlb": {
        "base": ["sports", "mlb", "baseball", "logo"],
    },
    "pixelfriends": {
        "base": ["emoji", "character", "pixel"],
    },
    "archon": {
        "base": ["emoji", "character", "fantasy"],
    },
    "anyboard": {
        "base": ["ui", "forum", "web"],
    },
    "businessicons": {
        "base": ["business", "office", "ui"],
    },
    "icatch21": {
        "base": ["ui", "set", "icon"],
    },
    "puzzle": {
        "base": ["files", "system", "folder"],
    },
    "internet": {
        "base": ["network", "web", "button"],
    },
    "gort": {
        "base": ["hardware", "device", "tool"],
    },
    "quicktime": {
        "base": ["media", "apple", "quicktime"],
    },
    "miscicon1": {
        "base": ["ui", "misc", "retro"],
    },
    "coffee": {
        "base": ["emoji", "coffee", "cup"],
    },
}

COLOR_WORDS = {
    "red", "blue", "green", "yellow", "orange", "purple", "violet",
    "pink", "gold", "silver", "black", "white", "gray", "grey",
    "brown", "cyan", "teal", "magenta", "navy", "maroon", "aqua"
}

EMOTION_WORDS = {
    "happy", "sad", "angry", "love", "mad", "grrr", "hello", "bunny",
    "cool", "panic", "friend", "friendly", "stress", "energy", "party",
    "nice", "remote", "snake", "bird"
}

STYLE_WORDS = {
    "pixel", "retro", "button", "badge", "icon", "glyph", "flat",
    "round", "outline", "symbol"
}

WORD_RE = re.compile(r"[^a-z0-9]+")


def normalize_slug(name: str) -> str:
    name = name.lower()
    name = WORD_RE.sub("-", name)
    return re.sub(r"-+", "-", name).strip("-")


def extract_words(slug: str) -> list[str]:
    return [w for w in WORD_RE.split(slug) if w]


def descriptor_tokens(slug: str, prefix: str) -> list[str]:
    desc: list[str] = []
    config = TARGET_PREFIXES.get(prefix)
    if config:
        desc.extend(config["base"])

    words = extract_words(slug)
    seen = set(desc)

    def add(token: str) -> None:
        token = token.strip("-")
        if not token or token in seen:
            return
        seen.add(token)
        desc.append(token)

    for word in words:
        if word in COLOR_WORDS:
            add(word)
        if word in EMOTION_WORDS:
            add(word)
        if word in STYLE_WORDS:
            add(word)
    return desc


def rename_file(path: Path) -> Path | None:
    stem = path.stem
    slug = normalize_slug(stem)
    parts = slug.split("-", 1)
    prefix = parts[0]
    if prefix not in TARGET_PREFIXES:
        return None

    descriptors = descriptor_tokens(slug, prefix)
    tokens = slug.split("-")
    existing = set(tokens)
    additions: list[str] = []
    for token in descriptors:
        if token not in existing:
            additions.append(token)
            existing.add(token)

    if not additions:
        return None

    new_slug = slug + "-" + "-".join(additions)
    target = path.with_name(new_slug + path.suffix.lower())
    counter = 2
    while target.exists():
        target = path.with_name(f"{new_slug}-{counter}{path.suffix.lower()}")
        counter += 1

    path.rename(target)
    return target


def main() -> None:
    renamed = []
    for file in sorted(RAW_DIR.glob("*.png")):
        result = rename_file(file)
        if result:
            renamed.append((file.name, result.name))
    print(f"Renamed {len(renamed)} files.")
    for old, new in renamed[:10]:
        print(f"  {old} -> {new}")


if __name__ == "__main__":
    main()
