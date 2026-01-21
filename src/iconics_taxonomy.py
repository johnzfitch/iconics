"""
Iconics taxonomy helpers.

This module is intentionally dependency-light so it can be imported by prompts,
labeling, catalog writing, and TUI code without pulling in heavy ML stacks.
"""

from __future__ import annotations

from typing import Dict, List, Optional

# Allowed categories (authoritative taxonomy for labeling).
# NOTE: SQLite stores category as free text, but the labeler constrains output to this list.
ALLOWED_CATEGORIES: List[str] = [
    # Core buckets
    "files",
    "network",
    "security",
    "tools",
    "ui",
    "emoji",
    "development",

    # Expanded buckets (to prevent "everything is ui")
    "communication",
    "media",
    "people",
    "commerce",
    "time",
    "system",
    "status",
    "navigation",

    # Higher-signal buckets for classic icon sets
    "apps",
    "brands",
    "devices",
    "data",
    "location",
    "weather",

    # Last-resort bucket (prefer anything else if reasonably applicable)
    "misc",
]

_ALLOWED_SET = set(ALLOWED_CATEGORIES)


def _normalize_category(raw: str) -> str:
    return (
        str(raw)
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )


# Accept common synonyms from VLM output and coerce into our taxonomy.
# IMPORTANT: This mapping exists to prevent "invalid category -> ui" collapse.
CATEGORY_ALIASES: Dict[str, str] = {
    # files
    "file": "files",
    "filesystem": "files",
    "folder": "files",
    "folders": "files",
    "document": "files",
    "documents": "files",
    "storage": "files",

    # network
    "net": "network",
    "networking": "network",
    "internet": "network",
    "wifi": "network",
    "wireless": "network",
    "cloud": "network",

    # security
    "secure": "security",
    "authentication": "security",
    "auth": "security",
    "lock": "security",
    "shield": "security",
    "certificate": "security",
    "key": "security",
    "privacy": "security",

    # tools
    "tool": "tools",
    "utility": "tools",
    "utilities": "tools",
    "gear": "tools",
    "wrench": "tools",

    # development
    "dev": "development",
    "developer": "development",
    "code": "development",
    "programming": "development",
    "terminal": "development",
    "console": "development",

    # emoji
    "emoticon": "emoji",
    "smiley": "emoji",
    "face": "emoji",

    # ui
    "user interface": "ui",
    "user-interface": "ui",
    "interface": "ui",

    # communication
    "email": "communication",
    "mail": "communication",
    "inbox": "communication",
    "message": "communication",
    "messages": "communication",
    "chat": "communication",
    "comment": "communication",
    "comments": "communication",
    "notification": "communication",
    "notifications": "communication",

    # media
    "video": "media",
    "audio": "media",
    "music": "media",
    "image": "media",
    "photo": "media",
    "camera": "media",
    "play": "media",

    # people
    "person": "people",
    "user": "people",
    "users": "people",
    "account": "people",
    "profile": "people",

    # commerce
    "money": "commerce",
    "payment": "commerce",
    "billing": "commerce",
    "cart": "commerce",
    "shopping": "commerce",

    # time
    "clock": "time",
    "calendar": "time",
    "date": "time",
    "timer": "time",

    # system
    "settings": "system",
    "power": "system",
    "battery": "system",
    "hardware": "system",
    "device": "devices",

    # status
    "warning": "status",
    "error": "status",
    "success": "status",
    "info": "status",

    # navigation
    "nav": "navigation",
    "arrow": "navigation",
    "arrows": "navigation",
    "back": "navigation",
    "forward": "navigation",
    "next": "navigation",
    "previous": "navigation",

    # apps
    "app": "apps",
    "application": "apps",
    "applications": "apps",
    "browser": "apps",
    "client": "apps",

    # brands
    "logo": "brands",
    "brand": "brands",

    # devices
    "devices": "devices",
    "hardware device": "devices",

    # data
    "database": "data",
    "analytics": "data",
    "metrics": "data",
    "chart": "data",
    "graph": "data",

    # location
    "map": "location",
    "maps": "location",
    "pin": "location",
    "marker": "location",
    "gps": "location",
    "location": "location",

    # weather
    "weather": "weather",
    "sun": "weather",
    "cloudy": "weather",
    "rain": "weather",
    "snow": "weather",
}


def coerce_category(
    raw_category: str,
    tags: Optional[List[str]] = None,
    candidates: Optional[List[Dict]] = None,
    *,
    fallback: str = "misc",
) -> str:
    """
    Coerce potentially-invalid model output into a valid catalog category.

    Order:
      1) exact allowed category
      2) alias mapping from common VLM terms
      3) infer from tags (high signal tokens)
      4) infer from retrieval candidates (prefer non-ui if present)
      5) fallback to 'misc' (not 'ui')
    """
    if raw_category in _ALLOWED_SET:
        return raw_category

    normalized = _normalize_category(raw_category)
    if normalized in CATEGORY_ALIASES:
        coerced = CATEGORY_ALIASES[normalized]
        if coerced in _ALLOWED_SET:
            return coerced

    # Tag-based inference (algorithm-first guardrail)
    tag_tokens: set[str] = set()
    if tags:
        for tag in tags:
            if isinstance(tag, str):
                tag_tokens.add(tag.strip().lower())

    if tag_tokens:
        if tag_tokens & {
            "email",
            "mail",
            "message",
            "chat",
            "comment",
            "notification",
            "inbox",
        }:
            return "communication"
        if tag_tokens & {
            "video",
            "audio",
            "music",
            "image",
            "photo",
            "camera",
            "play",
            "pause",
        }:
            return "media"
        if tag_tokens & {
            "user",
            "users",
            "account",
            "profile",
            "person",
            "people",
            "login",
            "logout",
        }:
            return "people"
        if tag_tokens & {
            "money",
            "payment",
            "billing",
            "cart",
            "shopping",
            "checkout",
            "coin",
            "dollar",
        }:
            return "commerce"
        if tag_tokens & {
            "clock",
            "calendar",
            "date",
            "time",
            "timer",
            "schedule",
            "alarm",
        }:
            return "time"
        if tag_tokens & {"settings", "power", "battery", "system"}:
            return "system"
        if tag_tokens & {"warning", "error", "success", "info", "alert", "caution", "critical"}:
            return "status"
        if tag_tokens & {"arrow", "back", "forward", "next", "previous", "home", "menu", "navigation"}:
            return "navigation"

        if tag_tokens & {"folder", "file", "files", "document", "documents", "directory", "archive", "pdf"}:
            return "files"
        if tag_tokens & {"network", "internet", "wifi", "cloud", "server", "connection", "globe"}:
            return "network"
        if tag_tokens & {"security", "secure", "lock", "shield", "key", "certificate", "auth", "password"}:
            return "security"
        if tag_tokens & {"tool", "tools", "gear", "wrench", "hammer", "utility"}:
            return "tools"
        if tag_tokens & {"dev", "development", "code", "terminal", "console", "git"}:
            return "development"
        if tag_tokens & {"emoji", "emoticon", "smiley", "face"}:
            return "emoji"

        if tag_tokens & {"app", "application", "applications", "browser", "client"}:
            return "apps"
        if tag_tokens & {"logo", "brand"}:
            return "brands"
        if tag_tokens & {
            "device",
            "devices",
            "iphone",
            "ipod",
            "phone",
            "tablet",
            "desktop",
            "laptop",
            "computer",
            "monitor",
            "printer",
        }:
            return "devices"
        if tag_tokens & {"data", "database", "db", "chart", "graph", "analytics", "metrics", "report", "table"}:
            return "data"
        if tag_tokens & {"location", "map", "pin", "marker", "gps", "compass"}:
            return "location"
        if tag_tokens & {"weather", "sun", "moon", "cloud", "rain", "snow", "storm", "wind"}:
            return "weather"

        # If the model didn't provide a valid category, only return 'ui' when tags say "ui".
        if tag_tokens & {"ui", "button", "checkbox", "radio", "toggle", "slider", "input", "form"}:
            return "ui"

    # Retrieval-based fallback: if we have strong neighbors, use the first non-ui category seen.
    if candidates:
        top = candidates[:5]
        cats = [c.get("category") for c in top if isinstance(c.get("category"), str)]
        cats = [c for c in cats if c in _ALLOWED_SET]
        non_ui = [c for c in cats if c != "ui"]
        if non_ui:
            return non_ui[0]
        if cats:
            return cats[0]

    return fallback if fallback in _ALLOWED_SET else "misc"
