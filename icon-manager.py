#!/usr/bin/env python3
"""
Iconics Manager - Semantic icon library management system
Manages the Iconics icon library for use across GitHub projects

Repository: https://github.com/johnzfitch/iconics
"""

import json
import os
import shutil
import argparse
import csv
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image

ICON_DIR = Path("/home/zack/dev/iconics")
CATALOG_FILE = ICON_DIR / "icon-catalog.json"
RAW_DIR = ICON_DIR / "raw"
CATALOG_DIR = ICON_DIR / "catalog"
HISTORY_FILE = ICON_DIR / ".icon-history.json"
ANALYTICS_FILE = ICON_DIR / ".icon-analytics.json"

class SemanticMatcher:
    """Advanced semantic matching with weighted scores and synonyms"""

    # Concept groups: related terms that should boost relevance
    CONCEPT_SYNONYMS = {
        # Security concepts
        'security': ['secure', 'protection', 'safety', 'guard', 'defend', 'safe'],
        'lock': ['padlock', 'locked', 'secure', 'closed', 'restrict'],
        'key': ['unlock', 'access', 'credential', 'password', 'auth'],
        'shield': ['protection', 'guard', 'defend', 'armor', 'secure'],
        'certificate': ['cert', 'ssl', 'tls', 'credential', 'verified', 'trust'],
        'authentication': ['auth', 'login', 'signin', 'credential', 'identity', 'user'],
        'password': ['credential', 'secret', 'auth', 'login', 'key'],

        # Network concepts
        'network': ['connection', 'internet', 'lan', 'wan', 'connectivity', 'web'],
        'cloud': ['server', 'hosting', 'storage', 'online', 'saas', 'remote'],
        'api': ['endpoint', 'rest', 'service', 'interface', 'integration'],
        'server': ['host', 'backend', 'service', 'machine', 'computer'],
        'wifi': ['wireless', 'network', 'connection', 'signal'],
        'globe': ['world', 'global', 'international', 'internet', 'web'],

        # Data concepts
        'database': ['db', 'data', 'storage', 'sql', 'records', 'table'],
        'storage': ['save', 'store', 'disk', 'drive', 'memory', 'persist'],
        'file': ['document', 'doc', 'data', 'content'],
        'folder': ['directory', 'dir', 'organize', 'container', 'files'],
        'document': ['doc', 'file', 'text', 'paper', 'page'],

        # UI concepts
        'warning': ['alert', 'caution', 'danger', 'error', 'attention', 'exclamation'],
        'error': ['fail', 'problem', 'issue', 'bug', 'warning', 'critical'],
        'success': ['done', 'complete', 'check', 'ok', 'approved', 'passed'],
        'info': ['information', 'help', 'about', 'details', 'notice'],
        'settings': ['config', 'configuration', 'options', 'preferences', 'setup'],
        'navigation': ['nav', 'menu', 'browse', 'explore', 'move'],

        # Actions
        'search': ['find', 'lookup', 'query', 'discover', 'magnify'],
        'edit': ['modify', 'change', 'update', 'write', 'pencil'],
        'delete': ['remove', 'trash', 'erase', 'clear', 'destroy'],
        'add': ['create', 'new', 'plus', 'insert', 'append'],
        'save': ['store', 'persist', 'keep', 'disk', 'write'],
        'download': ['get', 'fetch', 'receive', 'pull'],
        'upload': ['send', 'push', 'publish', 'share'],

        # Development
        'code': ['programming', 'dev', 'script', 'source', 'coding'],
        'terminal': ['console', 'shell', 'cli', 'command', 'prompt'],
        'bug': ['error', 'issue', 'debug', 'problem', 'defect'],
        'git': ['version', 'repo', 'branch', 'commit', 'vcs'],

        # Communication
        'email': ['mail', 'message', 'inbox', 'envelope', 'letter'],
        'chat': ['message', 'talk', 'conversation', 'im', 'communication'],
        'notification': ['alert', 'notice', 'bell', 'reminder'],

        # Media
        'image': ['picture', 'photo', 'graphic', 'visual', 'img'],
        'video': ['movie', 'film', 'media', 'play', 'recording'],
        'audio': ['sound', 'music', 'speaker', 'volume'],

        # Users
        'user': ['person', 'account', 'profile', 'member', 'people'],
        'admin': ['administrator', 'root', 'superuser', 'management'],

        # Office/Business (NEW)
        'office': ['business', 'work', 'corporate', 'professional', 'workplace', 'enterprise'],
        'business': ['office', 'corporate', 'enterprise', 'commercial', 'company'],
        'document': ['doc', 'file', 'paper', 'report', 'spreadsheet', 'presentation'],
        'spreadsheet': ['excel', 'sheet', 'table', 'data', 'grid', 'csv'],
        'presentation': ['slides', 'powerpoint', 'deck', 'slideshow'],

        # Media/Multimedia (NEW)
        'media': ['video', 'audio', 'multimedia', 'player', 'streaming', 'entertainment'],
        'player': ['media', 'play', 'video', 'audio', 'stream'],
        'camera': ['photo', 'capture', 'image', 'picture', 'snapshot', 'record'],

        # Hardware/Devices (NEW)
        'hardware': ['device', 'computer', 'machine', 'peripheral', 'equipment', 'component'],
        'device': ['hardware', 'gadget', 'machine', 'peripheral', 'equipment'],
        'computer': ['pc', 'desktop', 'laptop', 'machine', 'workstation', 'server'],
        'phone': ['mobile', 'cell', 'smartphone', 'telephone', 'call'],

        # Internet/Web (NEW)
        'internet': ['web', 'online', 'browser', 'www', 'http', 'website'],
        'browser': ['web', 'internet', 'chrome', 'firefox', 'safari', 'edge'],
        'website': ['web', 'page', 'site', 'online', 'portal'],

        # Applications/Software (NEW)
        'application': ['app', 'software', 'program', 'tool', 'utility', 'executable'],
        'software': ['app', 'application', 'program', 'tool'],
        'plugin': ['extension', 'addon', 'module', 'component'],

        # People/Social (NEW)
        'people': ['users', 'persons', 'humans', 'team', 'group', 'members'],
        'team': ['group', 'people', 'members', 'organization', 'staff'],
        'social': ['community', 'network', 'sharing', 'friends', 'followers'],

        # Status/States (NEW)
        'status': ['state', 'condition', 'indicator', 'signal'],
        'active': ['online', 'running', 'live', 'enabled', 'on'],
        'inactive': ['offline', 'stopped', 'disabled', 'off', 'paused'],
        'pending': ['waiting', 'queued', 'processing', 'loading'],

        # Actions/Operations (NEW)
        'run': ['execute', 'start', 'launch', 'play', 'begin'],
        'stop': ['halt', 'end', 'terminate', 'pause', 'quit'],
        'sync': ['synchronize', 'refresh', 'update', 'mirror'],
        'export': ['output', 'save', 'download', 'extract'],
        'import': ['input', 'load', 'upload', 'ingest'],

        # Commerce/Finance (NEW)
        'payment': ['pay', 'money', 'transaction', 'purchase', 'checkout'],
        'money': ['cash', 'currency', 'payment', 'finance', 'dollar'],
        'cart': ['shopping', 'basket', 'checkout', 'purchase', 'buy'],
        'credit': ['card', 'payment', 'finance', 'bank'],

        # Time/Calendar (NEW)
        'time': ['clock', 'timer', 'schedule', 'duration', 'period'],
        'calendar': ['schedule', 'date', 'event', 'appointment', 'planner'],
        'clock': ['time', 'timer', 'watch', 'hour', 'minute'],

        # Themes/Appearance (NEW)
        'dark': ['night', 'black', 'theme', 'mode'],
        'light': ['day', 'white', 'bright', 'theme', 'mode'],
        'theme': ['style', 'appearance', 'skin', 'mode'],

        # Containers/Organization (NEW)
        'container': ['box', 'package', 'wrapper', 'holder'],
        'archive': ['zip', 'compress', 'backup', 'bundle', 'package'],
        'package': ['bundle', 'archive', 'module', 'library'],
    }

    # Context mappings: what concepts to prioritize for given contexts
    CONTEXT_WEIGHTS = {
        'authentication': {
            'lock': 0.95, 'key': 0.90, 'shield': 0.85, 'certificate': 0.80,
            'login': 0.95, 'user': 0.75, 'password': 0.88, 'credential': 0.85,
            'secure': 0.70, 'protection': 0.65, 'identity': 0.82
        },
        'security': {
            'shield': 0.95, 'lock': 0.92, 'key': 0.88, 'protection': 0.90,
            'certificate': 0.82, 'secure': 0.85, 'guard': 0.78, 'keychain': 0.75,
            'firewall': 0.80, 'encrypted': 0.85
        },
        'network': {
            'network': 0.95, 'cloud': 0.88, 'globe': 0.85, 'wifi': 0.82,
            'server': 0.80, 'connection': 0.90, 'internet': 0.88, 'web': 0.75,
            'router': 0.78, 'ethernet': 0.72
        },
        'api': {
            'network': 0.88, 'cloud': 0.85, 'server': 0.90, 'database': 0.82,
            'endpoint': 0.92, 'integration': 0.80, 'connection': 0.78
        },
        'data': {
            'database': 0.95, 'folder': 0.85, 'storage': 0.90, 'cloud': 0.80,
            'file': 0.82, 'document': 0.78, 'save': 0.75, 'disk': 0.72
        },
        'database': {
            'database': 0.98, 'storage': 0.85, 'server': 0.80, 'data': 0.88,
            'table': 0.82, 'sql': 0.78, 'records': 0.75
        },
        'error': {
            'warning': 0.92, 'error': 0.98, 'alert': 0.88, 'danger': 0.85,
            'bug': 0.80, 'problem': 0.82, 'critical': 0.78, 'fail': 0.85
        },
        'warning': {
            'warning': 0.98, 'alert': 0.92, 'caution': 0.88, 'danger': 0.85,
            'exclamation': 0.82, 'attention': 0.80, 'notice': 0.75
        },
        'success': {
            'checkbox': 0.92, 'checkmark': 0.95, 'success': 0.98, 'done': 0.90,
            'complete': 0.88, 'approved': 0.85, 'ok': 0.82, 'good': 0.75
        },
        'info': {
            'info': 0.98, 'help': 0.90, 'question': 0.85, 'about': 0.82,
            'details': 0.78, 'information': 0.95, 'notice': 0.72
        },
        'settings': {
            'settings': 0.98, 'options': 0.92, 'gear': 0.88, 'toolbox': 0.85,
            'config': 0.95, 'preferences': 0.82, 'setup': 0.78, 'control': 0.75
        },
        'navigation': {
            'home': 0.90, 'menu': 0.92, 'arrow': 0.88, 'close': 0.75,
            'navigation': 0.98, 'browse': 0.82, 'back': 0.85, 'forward': 0.85
        },
        'files': {
            'folder': 0.95, 'document': 0.92, 'file': 0.98, 'pdf': 0.85,
            'documents': 0.90, 'archive': 0.78, 'text': 0.75
        },
        'development': {
            'console': 0.92, 'terminal': 0.90, 'code': 0.95, 'script': 0.88,
            'database': 0.85, 'git': 0.82, 'bug': 0.78, 'api': 0.80
        },
        'search': {
            'search': 0.98, 'find': 0.95, 'magnifying': 0.85, 'lookup': 0.90,
            'query': 0.82, 'discover': 0.78
        },
        'user': {
            'user': 0.98, 'profile': 0.92, 'account': 0.90, 'person': 0.88,
            'login': 0.82, 'logout': 0.80, 'avatar': 0.78
        },
        'email': {
            'email': 0.98, 'mail': 0.95, 'envelope': 0.90, 'message': 0.85,
            'inbox': 0.88, 'letter': 0.82, 'send': 0.75
        },
        # NEW CONTEXT WEIGHTS
        'office': {
            'document': 0.95, 'spreadsheet': 0.92, 'presentation': 0.90, 'folder': 0.88,
            'file': 0.85, 'business': 0.82, 'office': 0.98, 'work': 0.75
        },
        'media': {
            'video': 0.95, 'audio': 0.92, 'player': 0.90, 'media': 0.98,
            'camera': 0.88, 'photo': 0.85, 'music': 0.82, 'stream': 0.78
        },
        'hardware': {
            'computer': 0.95, 'device': 0.92, 'hardware': 0.98, 'peripheral': 0.88,
            'disk': 0.85, 'drive': 0.82, 'monitor': 0.80, 'keyboard': 0.78
        },
        'commerce': {
            'cart': 0.95, 'payment': 0.92, 'money': 0.90, 'credit': 0.88,
            'shop': 0.85, 'purchase': 0.82, 'checkout': 0.90, 'transaction': 0.85
        },
        'calendar': {
            'calendar': 0.98, 'schedule': 0.92, 'date': 0.88, 'event': 0.85,
            'time': 0.80, 'clock': 0.78, 'appointment': 0.82
        },
        'social': {
            'people': 0.92, 'team': 0.90, 'social': 0.98, 'user': 0.85,
            'group': 0.88, 'community': 0.82, 'share': 0.78
        },
        'status': {
            'success': 0.92, 'error': 0.92, 'warning': 0.90, 'info': 0.88,
            'status': 0.98, 'active': 0.85, 'pending': 0.82, 'indicator': 0.80
        },
        'theme': {
            'dark': 0.92, 'light': 0.92, 'theme': 0.98, 'style': 0.85,
            'appearance': 0.82, 'color': 0.78, 'mode': 0.88
        },
    }

    # Aliases for context lookup
    CONTEXT_ALIASES = {
        'auth': 'authentication', 'login': 'authentication', 'signin': 'authentication',
        'secure': 'security', 'protection': 'security',
        'connection': 'network', 'internet': 'network', 'web': 'network', 'server': 'network',
        'storage': 'data', 'db': 'database',
        'alert': 'warning', 'caution': 'warning', 'danger': 'error',
        'complete': 'success', 'done': 'success', 'check': 'success',
        'help': 'info', 'information': 'info', 'about': 'info',
        'config': 'settings', 'options': 'settings', 'preferences': 'settings',
        'nav': 'navigation', 'menu': 'navigation', 'ui': 'navigation',
        'documents': 'files', 'docs': 'files', 'folder': 'files',
        'code': 'development', 'programming': 'development', 'coding': 'development',
        'find': 'search', 'lookup': 'search',
        'account': 'user', 'profile': 'user', 'person': 'user',
        'mail': 'email', 'message': 'email',
        # NEW ALIASES
        'business': 'office', 'work': 'office', 'corporate': 'office', 'professional': 'office',
        'video': 'media', 'audio': 'media', 'multimedia': 'media', 'streaming': 'media',
        'device': 'hardware', 'computer': 'hardware', 'peripheral': 'hardware', 'equipment': 'hardware',
        'payment': 'commerce', 'money': 'commerce', 'shop': 'commerce', 'shopping': 'commerce', 'checkout': 'commerce',
        'schedule': 'calendar', 'date': 'calendar', 'event': 'calendar', 'appointment': 'calendar',
        'team': 'social', 'group': 'social', 'people': 'social', 'community': 'social',
        'state': 'status', 'indicator': 'status', 'condition': 'status',
        'dark': 'theme', 'light': 'theme', 'mode': 'theme', 'appearance': 'theme', 'style': 'theme',
    }

    # Negative terms: concepts that should NOT match for a given context
    CONTEXT_NEGATIVE = {
        'security': {'clock', 'time', 'alarm', 'hour', 'minute', 'color', 'transparency'},
        'authentication': {'clock', 'time', 'alarm', 'hour', 'minute', 'flow', 'flip'},
        'network': {'time', 'clock', 'alarm'},
        'data': {'time', 'clock', 'alarm'},
        'files': {'time', 'clock', 'alarm'},
        'development': {'time', 'clock', 'alarm'},
    }

    @classmethod
    def get_synonyms(cls, term: str) -> set:
        """Get all synonyms for a term"""
        term_lower = term.lower()
        synonyms = {term_lower}

        # Direct synonyms
        if term_lower in cls.CONCEPT_SYNONYMS:
            synonyms.update(cls.CONCEPT_SYNONYMS[term_lower])

        # Reverse lookup: find terms that have this as a synonym
        for key, values in cls.CONCEPT_SYNONYMS.items():
            if term_lower in values:
                synonyms.add(key)
                synonyms.update(values)

        return synonyms

    @classmethod
    def resolve_context(cls, context: str) -> str:
        """Resolve context aliases to canonical form"""
        context_lower = context.lower()
        return cls.CONTEXT_ALIASES.get(context_lower, context_lower)

    @classmethod
    def calculate_match_score(cls, icon: dict, query: str, context: str = None) -> float:
        """
        Calculate match score (0.0 - 1.0) for an icon against a query/context

        Scoring factors:
        - Direct tag match: base score
        - Semantic name match: high score
        - Synonym matches: partial score
        - Context relevance: weighted boost
        """
        import re

        score = 0.0
        query_lower = query.lower()
        query_synonyms = cls.get_synonyms(query)

        semantic_name = icon.get('semanticName', '').lower()
        tags = [t.lower() for t in icon.get('tags', [])]
        description = icon.get('description', '').lower()

        # Helper: check for word boundary match (avoid "clock" matching "lock")
        def word_match(needle: str, haystack: str) -> bool:
            """Check if needle matches as a whole word in haystack"""
            # Match at word boundaries
            pattern = r'\b' + re.escape(needle) + r'\b'
            return bool(re.search(pattern, haystack))

        def word_in_compound(needle: str, haystack: str) -> bool:
            """Check if needle is a meaningful component of haystack (e.g., 'lock' in 'unlock')"""
            # Known meaningful prefixes/suffixes for compound words
            valid_prefixes = {'un', 'open', 're', 'pre', 'anti', 'non', 'auto', 'over', 'under'}
            valid_suffixes = {'ing', 'ed', 's', 'er', 'es'}

            if haystack == needle:
                return True

            # Check if it's a prefix+needle pattern (e.g., "unlock" = "un" + "lock")
            if haystack.endswith(needle):
                prefix = haystack[:-len(needle)]
                if prefix in valid_prefixes:
                    return True

            # Check if it's needle+suffix pattern
            if haystack.startswith(needle):
                suffix = haystack[len(needle):]
                if suffix in valid_suffixes or suffix.startswith('-'):
                    return True

            # Check for hyphenated compounds
            if f'-{needle}' in haystack or f'{needle}-' in haystack:
                return True

            return False

        # Exact semantic name match = highest score
        if query_lower == semantic_name:
            score = 0.98
        elif word_match(query_lower, semantic_name):
            score = max(score, 0.85)
        elif word_in_compound(query_lower, semantic_name):
            score = max(score, 0.75)

        # Tag matching - require exact or word boundary matches
        for tag in tags:
            if query_lower == tag:
                score = max(score, 0.90)
            elif word_match(query_lower, tag) or word_match(tag, query_lower):
                score = max(score, 0.70)
            elif tag in query_synonyms:
                score = max(score, 0.65)

        # Synonym matching in semantic name - require word boundary
        for syn in query_synonyms:
            if word_match(syn, semantic_name) or word_in_compound(syn, semantic_name):
                score = max(score, 0.72)
            if word_match(syn, description):
                score = max(score, 0.48)

        # Context-based scoring - use word boundary matching
        if context:
            resolved_context = cls.resolve_context(context)
            if resolved_context in cls.CONTEXT_WEIGHTS:
                context_weights = cls.CONTEXT_WEIGHTS[resolved_context]

                # Check semantic name against context weights
                for weighted_term, weight in context_weights.items():
                    if word_match(weighted_term, semantic_name) or word_in_compound(weighted_term, semantic_name):
                        score = max(score, weight)
                    for tag in tags:
                        if weighted_term == tag:
                            score = max(score, weight * 0.95)
                        elif word_match(weighted_term, tag):
                            score = max(score, weight * 0.90)

        # Penalize size-only tags and generic icons
        size_tags = {'16x16', '24x24', '32x32', '48x48', '128x128', '12x12', '256x256'}
        non_size_tags = [t for t in tags if t not in size_tags and t not in {'icon', 'generic', 'ui-element', 'numbered'}]
        if len(non_size_tags) == 0 and score > 0:
            score *= 0.5  # Penalize icons with only generic tags

        # Apply negative term filtering for context
        if context and score > 0:
            resolved_context = cls.resolve_context(context)
            negative_terms = cls.CONTEXT_NEGATIVE.get(resolved_context, set())
            for neg_term in negative_terms:
                if neg_term in semantic_name or any(neg_term in t for t in tags):
                    score *= 0.1  # Heavy penalty for negative matches
                    break

        return min(score, 1.0)

    @classmethod
    def rank_icons(cls, icons: list, query: str, context: str = None, min_score: float = 0.3) -> list:
        """
        Rank icons by relevance score

        Returns: List of (icon, score) tuples sorted by score descending
        """
        scored = []
        for icon in icons:
            score = cls.calculate_match_score(icon, query, context)
            if score >= min_score:
                scored.append((icon, score))

        return sorted(scored, key=lambda x: -x[1])


class EmojiMapper:
    """Maps common emojis to semantic icon names for README migration"""

    # Emoji to icon semantic name mappings
    EMOJI_TO_ICON = {
        # Folders/Files
        '📁': 'folder',
        '📂': 'folder-open',
        '📄': 'document',
        '📃': 'document',
        '📋': 'clipboard',
        '📝': 'edit',
        '📖': 'book',
        '📚': 'books',

        # Security
        '🔒': 'lock',
        '🔓': 'unlock',
        '🔐': 'lock',
        '🔑': 'key',
        '🛡️': 'shield',
        '🛡': 'shield',

        # Status/Indicators
        '✅': 'checkbox',
        '✓': 'checkmark',
        '❌': 'error',
        '❎': 'cancel',
        '⚠️': 'warning',
        '⚠': 'warning',
        '⛔': 'stop',
        '🚫': 'prohibited',
        '❓': 'question',
        '❔': 'question',
        'ℹ️': 'info',
        'ℹ': 'info',

        # Severity/Priority
        '🔴': 'status-red',
        '🟠': 'status-orange',
        '🟡': 'status-yellow',
        '🟢': 'status-green',
        '🔵': 'status-blue',

        # Actions
        '🚀': 'rocket',
        '⬆️': 'arrow-up',
        '⬇️': 'arrow-down',
        '➡️': 'arrow-right',
        '⬅️': 'arrow-left',
        '🔄': 'refresh',
        '🔃': 'sync',
        '💾': 'save',
        '📥': 'download',
        '📤': 'upload',
        '🔍': 'search',
        '🔎': 'search',

        # Tools/Settings
        '🔧': 'toolbox',
        '🛠️': 'tools',
        '🛠': 'tools',
        '⚙️': 'settings',
        '⚙': 'settings',
        '🔩': 'component',

        # Network/Web
        '🌐': 'globe',
        '🌍': 'globe',
        '🌎': 'globe',
        '🌏': 'globe',
        '☁️': 'cloud',
        '☁': 'cloud',
        '📡': 'network-signal',
        '🔗': 'link',

        # Communication
        '📧': 'email',
        '✉️': 'envelope',
        '💬': 'chat',
        '💭': 'thought',
        '📢': 'announcement',
        '🔔': 'notification',
        '📞': 'phone',

        # Data/Analytics
        '📊': 'chart',
        '📈': 'chart-up',
        '📉': 'chart-down',
        '🗃️': 'database',
        '🗄️': 'archive',

        # Media
        '🖼️': 'image',
        '📷': 'camera',
        '📸': 'camera',
        '🎬': 'video',
        '🎥': 'video-camera',
        '🎵': 'audio',
        '🎶': 'music',

        # Time
        '⏰': 'clock',
        '🕐': 'clock',
        '📅': 'calendar',
        '⏱️': 'timer',

        # People/Users
        '👤': 'user',
        '👥': 'users',
        '👋': 'wave',
        '🙋': 'help',

        # Misc
        '⚖️': 'balance',
        '💡': 'idea',
        '🎯': 'target',
        '🏷️': 'tag',
        '⭐': 'star',
        '🌟': 'star',
        '❤️': 'heart',
        '💥': 'explosion',
        '🔥': 'fire',
        '✨': 'sparkle',
        '💎': 'diamond',
        '🎉': 'celebration',
        '🎊': 'confetti',
    }

    # Reverse mapping for suggesting emojis to replace
    ICON_TO_EMOJI = {v: k for k, v in EMOJI_TO_ICON.items()}

    @classmethod
    def find_emojis_in_text(cls, text: str) -> list:
        """Find all recognized emojis in text and suggest replacements"""
        import re
        found = []

        for emoji, icon_name in cls.EMOJI_TO_ICON.items():
            if emoji in text:
                # Find all occurrences with context
                for match in re.finditer(re.escape(emoji), text):
                    # Get surrounding context
                    start = max(0, match.start() - 30)
                    end = min(len(text), match.end() + 30)
                    context = text[start:end].replace('\n', ' ')

                    found.append({
                        'emoji': emoji,
                        'icon': icon_name,
                        'position': match.start(),
                        'context': f"...{context}..."
                    })

        return sorted(found, key=lambda x: x['position'])

    @classmethod
    def generate_replacement_markdown(cls, icon_name: str, project_path: str = None) -> str:
        """Generate markdown replacement for an emoji"""
        if project_path:
            return f"![{icon_name}](.github/assets/icons/{icon_name}.png)"
        return f"![{icon_name}](icons/{icon_name}.png)"

    @classmethod
    def scan_readme(cls, readme_path: str) -> dict:
        """Scan a README file for emoji replacements"""
        from pathlib import Path

        path = Path(readme_path)
        if not path.exists():
            return {'error': f'File not found: {readme_path}'}

        content = path.read_text(errors='ignore')
        emojis_found = cls.find_emojis_in_text(content)

        # Group by icon name
        by_icon = {}
        for item in emojis_found:
            icon = item['icon']
            if icon not in by_icon:
                by_icon[icon] = {'emoji': item['emoji'], 'count': 0, 'contexts': []}
            by_icon[icon]['count'] += 1
            if len(by_icon[icon]['contexts']) < 3:
                by_icon[icon]['contexts'].append(item['context'])

        return {
            'file': str(path),
            'total_emojis': len(emojis_found),
            'unique_icons_needed': len(by_icon),
            'replacements': by_icon
        }


class GalleryGenerator:
    """Generates a static HTML gallery for the icon library"""

    HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Iconics Gallery</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <style>
        :root {
            --bg: #f8f9fa;
            --card-bg: #ffffff;
            --text: #212529;
            --primary: #0d6efd;
        }
        body { font-family: system-ui, -apple-system, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 2rem; }
        h1 { text-align: center; }
        .controls { position: sticky; top: 0; background: var(--bg); padding: 1rem; z-index: 100; display: flex; gap: 1rem; justify-content: center; border-bottom: 1px solid #dee2e6; margin-bottom: 2rem; }
        input { padding: 0.5rem 1rem; border: 1px solid #ced4da; border-radius: 0.25rem; width: 300px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 1.5rem; }
        .icon-card { background: var(--card-bg); border-radius: 0.5rem; padding: 1rem; text-align: center; box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075); transition: transform 0.2s; cursor: pointer; }
        .icon-card:hover { transform: translateY(-5px); box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.15); }
        .icon-card img { width: 64px; height: 64px; image-rendering: pixelated; margin-bottom: 0.5rem; }
        .icon-name { font-size: 0.875rem; font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .icon-meta { font-size: 0.75rem; color: #6c757d; margin-top: 0.25rem; }
        .category-section { margin-bottom: 3rem; }
        .category-title { border-bottom: 2px solid var(--primary); padding-bottom: 0.5rem; margin-bottom: 1.5rem; text-transform: uppercase; letter-spacing: 0.1em; }
        
        /* HTMX transition styles */
        .icon-card.htmx-swapping { opacity: 0; transition: opacity 0.2s ease-out; }
    </style>
</head>
<body hx-boost="true">
    <h1>Iconics Library Gallery</h1>
    <div class="controls">
        <input type="text" id="search" name="q" placeholder="Search icons..." 
               onkeyup="filterIcons()"
               hx-trigger="keyup changed delay:200ms"
               hx-target="#gallery"
               hx-select="#gallery">
        <select id="categoryFilter" name="category" onchange="filterIcons()"
                hx-trigger="change"
                hx-target="#gallery"
                hx-select="#gallery">
            <option value="all">All Categories</option>
            {category_options}
        </select>
    </div>
    <div id="gallery">
        {content}
    </div>
    <script>
        // Enhanced filtering with smooth transitions
        function filterIcons() {
            const query = document.getElementById('search').value.toLowerCase();
            const category = document.getElementById('categoryFilter').value;
            const sections = document.querySelectorAll('.category-section');
            
            sections.forEach(section => {
                const sectionCat = section.getAttribute('data-cat');
                const cards = section.querySelectorAll('.icon-card');
                let hasVisibleCards = false;
                
                const catMatches = category === 'all' || category === sectionCat;
                
                if (!catMatches) {
                    section.style.display = 'none';
                    return;
                }
                
                cards.forEach(card => {
                    const name = card.getAttribute('data-name');
                    const tags = card.getAttribute('data-tags');
                    const matchesSearch = name.includes(query) || tags.includes(query);
                    
                    card.style.display = matchesSearch ? 'block' : 'none';
                    if (matchesSearch) hasVisibleCards = true;
                });
                
                section.style.display = hasVisibleCards ? 'block' : 'none';
            });
        }
        
        function copyCommand(name) {
            const cmd = `icon use ${name}`;
            navigator.clipboard.writeText(cmd);
            const feedback = document.createElement('div');
            feedback.style.position = 'fixed';
            feedback.style.bottom = '2rem';
            feedback.style.left = '50%';
            feedback.style.transform = 'translateX(-50%)';
            feedback.style.background = '#198754';
            feedback.style.color = 'white';
            feedback.style.padding = '0.5rem 1.5rem';
            feedback.style.borderRadius = '2rem';
            feedback.style.zIndex = '1000';
            feedback.textContent = `Copied: ${cmd}`;
            document.body.appendChild(feedback);
            setTimeout(() => feedback.remove(), 2000);
        }
    </script>
</body>
</html>
"""

    @classmethod
    def generate(cls, catalog: dict, output_path: Path):
        categories = sorted(catalog.get("categories", []))
        category_options = "".join([f'<option value="{c}">{c.title()}</option>' for c in categories])
        
        # Group icons by category
        by_category = {}
        for icon in catalog["icons"]:
            cat = icon.get("category", "ui")
            if cat not in by_category: by_category[cat] = []
            by_category[cat].append(icon)
            
        content_html = ""
        for cat in sorted(by_category.keys()):
            content_html += f'<div class="category-section" data-cat="{cat}">'
            content_html += f'<h2 class="category-title">{cat}</h2>'
            content_html += '<div class="grid">'
            
            # Sort icons in category
            sorted_icons = sorted(by_category[cat], key=lambda x: x["semanticName"])
            for icon in sorted_icons:
                name = icon["semanticName"]
                tags = ",".join(icon.get("tags", []))
                # Use relative path for local viewing
                img_path = f"raw/{icon['id']}.png"
                content_html += f"""
                <div class="icon-card" data-name="{name.lower()}" data-tags="{tags.lower()}" data-category="{cat}" onclick="copyCommand('{name}')">
                    <img src="{img_path}" alt="{name}">
                    <div class="icon-name">{name}</div>
                    <div class="icon-meta">#{icon['id']}</div>
                </div>"""
            
            content_html += "</div></div>"
            
        full_html = cls.HTML_TEMPLATE.replace("{category_options}", category_options).replace("{content}", content_html)
        output_path.write_text(full_html)
        return True


class IconManager:
    def __init__(self):
        self.catalog = self.load_catalog()
        self.matcher = SemanticMatcher()

    def load_catalog(self) -> Dict:
        """Load icon catalog from JSON file"""
        if CATALOG_FILE.exists():
            with open(CATALOG_FILE, 'r') as f:
                return json.load(f)
        return {
            "version": "1.0",
            "icons": [],
            "categories": ["files", "network", "security", "tools", "ui", "emoji", "development"]
        }

    def save_catalog(self):
        """Save catalog to JSON file"""
        with open(CATALOG_FILE, 'w') as f:
            json.dump(self.catalog, f, indent=2)
        print(f"✓ Catalog saved to {CATALOG_FILE}")

    def find_icon_by_id(self, icon_id: str) -> Optional[Dict]:
        """Find icon in catalog by numeric ID"""
        for icon in self.catalog["icons"]:
            if icon["id"] == icon_id:
                return icon
        return None

    def find_icons_by_tag(self, tag: str) -> List[Dict]:
        """Find all icons matching a tag"""
        tag_lower = tag.lower()
        return [icon for icon in self.catalog["icons"]
                if tag_lower in [t.lower() for t in icon.get("tags", [])]]

    def find_icons_by_semantic(self, name: str) -> List[Dict]:
        """Find icons by semantic name with ranked matching"""
        name_lower = name.lower()

        # Categorize matches by quality
        exact_matches = []      # Exact semantic name
        prefix_matches = []     # Starts with query
        suffix_matches = []     # Ends with query (e.g., checkmark for check)
        contains_matches = []   # Contains query anywhere

        for icon in self.catalog["icons"]:
            semantic = icon.get("semanticName", "").lower()
            if semantic == name_lower:
                exact_matches.append(icon)
            elif semantic.startswith(name_lower + "-") or semantic.startswith(name_lower):
                prefix_matches.append(icon)
            elif semantic.endswith(name_lower) or semantic.endswith("-" + name_lower):
                suffix_matches.append(icon)
            elif name_lower in semantic:
                contains_matches.append(icon)

        # Return in priority order: exact > prefix > suffix > contains
        return exact_matches + prefix_matches + suffix_matches + contains_matches

    def get_fuzzy_terms(self, query: str) -> List[str]:
        """Expand query to include fuzzy-matched related terms"""
        query_lower = query.lower()
        terms = [query_lower]

        # Common suffixes to try
        suffixes = ['mark', 'box', 'ing', 'ed', 's', 'er', 'tion', 'icon', 'file', 'folder']
        prefixes = ['un', 're', 'pre', 'post', 'out', 'in']

        # Add variations with suffixes
        for suffix in suffixes:
            variant = query_lower + suffix
            if variant not in terms:
                terms.append(variant)

        # Common term expansions (synonym-like)
        expansions = {
            'check': ['checkmark', 'checkbox', 'tick', 'verify', 'done'],
            'book': ['notebook', 'manual', 'documentation', 'guide'],
            'lock': ['padlock', 'secure', 'locked'],
            'folder': ['directory', 'dir'],
            'file': ['document', 'doc'],
            'arrow': ['pointer', 'direction'],
            'user': ['person', 'profile', 'account'],
            'settings': ['config', 'configuration', 'options', 'preferences'],
            'search': ['find', 'lookup', 'magnify'],
            'error': ['warning', 'alert', 'danger'],
            'info': ['information', 'help', 'about'],
            'home': ['house', 'main'],
            'mail': ['email', 'envelope', 'message'],
            'phone': ['telephone', 'call', 'mobile'],
            'cloud': ['upload', 'download', 'sync'],
            'star': ['favorite', 'bookmark', 'rating'],
            'heart': ['favorite', 'love', 'like'],
            'trash': ['delete', 'remove', 'garbage', 'bin'],
            'save': ['disk', 'floppy'],
            'edit': ['pencil', 'pen', 'modify'],
            'add': ['plus', 'new', 'create'],
            'remove': ['minus', 'delete', 'close'],
        }

        if query_lower in expansions:
            terms.extend(expansions[query_lower])

        # Also check reverse (if searching for 'checkmark', also try 'check')
        for base, variants in expansions.items():
            if query_lower in variants:
                terms.append(base)

        return list(set(terms))  # Remove duplicates

    def search(self, query: str) -> List[Dict]:
        """Search icons by tag or semantic name with fuzzy matching"""
        results = []
        scored_results = {}  # id -> (icon, score)

        # Get expanded search terms
        terms = self.get_fuzzy_terms(query)
        query_lower = query.lower()

        for term in terms:
            # Higher score for exact query, lower for fuzzy matches
            score_multiplier = 1.0 if term == query_lower else 0.7

            for icon in self.find_icons_by_tag(term):
                icon_id = icon["id"]
                # Exact tag match gets bonus
                tag_bonus = 0.3 if term in [t.lower() for t in icon.get("tags", [])] else 0
                score = (0.8 + tag_bonus) * score_multiplier
                if icon_id not in scored_results or scored_results[icon_id][1] < score:
                    scored_results[icon_id] = (icon, score)

            for icon in self.find_icons_by_semantic(term):
                icon_id = icon["id"]
                semantic = icon.get("semanticName", "").lower()
                # Score based on match quality
                if semantic == term:
                    base_score = 1.0  # Exact match
                elif semantic.startswith(term):
                    base_score = 0.9  # Prefix match
                elif semantic.endswith(term):
                    base_score = 0.8  # Suffix match
                else:
                    base_score = 0.6  # Contains match
                score = base_score * score_multiplier
                if icon_id not in scored_results or scored_results[icon_id][1] < score:
                    scored_results[icon_id] = (icon, score)

        # Sort by score descending
        sorted_results = sorted(scored_results.values(), key=lambda x: x[1], reverse=True)
        return [icon for icon, score in sorted_results]

    def suggest(self, context: str, limit: int = 10) -> List[tuple]:
        """
        Get icon suggestions for a context with relevance scores

        Args:
            context: The context/topic to suggest icons for (e.g., 'security', 'authentication')
            limit: Maximum number of suggestions to return

        Returns:
            List of (icon, score) tuples sorted by relevance
        """
        # Score all icons against the context
        ranked = SemanticMatcher.rank_icons(
            self.catalog["icons"],
            context,
            context=context,
            min_score=0.30
        )

        return ranked[:limit]

    def suggest_formatted(self, context: str, limit: int = 10) -> str:
        """
        Get formatted icon suggestions with percentage scores

        Returns human-readable string output
        """
        # Get more suggestions than needed so we can dedupe
        suggestions = self.suggest(context, limit * 3)

        if not suggestions:
            return f"No icons found for context '{context}'"

        lines = [f"\nIcon suggestions for '{context}':\n"]

        # Deduplicate by semantic name, keeping highest score
        seen_names = set()
        deduped = []
        for icon, score in suggestions:
            name = icon['semanticName']
            if name not in seen_names:
                seen_names.add(name)
                deduped.append((icon, score))
                if len(deduped) >= limit:
                    break

        # Filter out size tags for cleaner display
        size_tags = {'16x16', '24x24', '32x32', '48x48', '128x128', '12x12', '256x256',
                     'icon', 'generic', 'ui-element', 'numbered'}

        for icon, score in deduped:
            pct = int(score * 100)
            name = icon['semanticName']
            # Filter tags for display
            display_tags = [t for t in icon.get('tags', []) if t.lower() not in size_tags][:4]
            tags_str = ', '.join(display_tags) if display_tags else icon['category']
            lines.append(f"  {name:20} ({pct:2}%)  [{icon['category']}]  {tags_str}")

        lines.append(f"\nUse: icon use <name> to export and get markdown")

        return '\n'.join(lines)

    def add_icon(self, icon_id: str, semantic_name: str, tags: List[str],
                 category: str, description: str = "", save: bool = True,
                 metaphor: str = "", valence: float = 0.0, abstraction: int = 1,
                 variant_of: str = "", style: str = "silk", confidence: float = 1.0):
        """Add or update icon in catalog with Schema 2.1 features"""
        existing = self.find_icon_by_id(icon_id)

        icon_data = {
            "id": icon_id,
            "filename": f"raw/{icon_id}.png",
            "semanticName": semantic_name,
            "tags": tags,
            "category": category,
            "description": description,
            "style": style or (existing.get("style") if existing else "silk"),
            "metaphor": metaphor or (existing.get("metaphor") if existing else ""),
            "emotional_valence": valence if valence != 0.0 else (existing.get("emotional_valence", 0.0) if existing else 0.0),
            "abstraction_level": abstraction if abstraction != 1 else (existing.get("abstraction_level", 1) if existing else 1),
            "variant_of": variant_of or (existing.get("variant_of") if existing else ""),
            "enrichment_confidence": confidence if confidence != 1.0 else (existing.get("enrichment_confidence", 1.0) if existing else 1.0),
            "usedIn": existing.get("usedIn", []) if existing else []
        }

        if existing:
            idx = self.catalog["icons"].index(existing)
            self.catalog["icons"][idx] = icon_data
            # print(f"✓ Updated icon {icon_id}")
        else:
            self.catalog["icons"].append(icon_data)
            # print(f"✓ Added icon {icon_id}")

        self.create_symlink(icon_id, semantic_name, category)
        if save:
            self.save_catalog()

    def create_symlink(self, icon_id: str, semantic_name: str, category: str):
        """Create symlink in catalog/category/ directory"""
        category_dir = CATALOG_DIR / category
        category_dir.mkdir(parents=True, exist_ok=True)

        source = RAW_DIR / f"{icon_id}.png"
        target = category_dir / f"{semantic_name}.png"

        if target.exists() or target.is_symlink():
            target.unlink()

        if source.exists():
            target.symlink_to(f"../../raw/{icon_id}.png")
            # print(f"  → Created symlink: catalog/{category}/{semantic_name}.png") # Too noisy for bulk

    def list_category(self, category: str):
        """List all icons in a category"""
        icons = [icon for icon in self.catalog["icons"]
                 if icon.get("category") == category]

        if not icons:
            print(f"No icons found in category '{category}'")
            return

        print(f"\n{category.upper()} ({len(icons)} icons):")
        print("-" * 60)
        for icon in sorted(icons, key=lambda x: x["semanticName"]):
            tags_str = ", ".join(icon.get("tags", []))
            print(f"  {icon['semanticName']:20} (#{icon['id']})  Tags: {tags_str}")

    def export_to_project(self, project_path: str, icon_names: List[str]):
        """Export icons to a project's .github/assets/icons/ directory"""
        project = Path(project_path)
        icon_dir = project / ".github" / "assets" / "icons"
        icon_dir.mkdir(parents=True, exist_ok=True)

        exported = []
        for name in icon_names:
            # Find icon by semantic name
            icons = self.find_icons_by_semantic(name)
            if not icons:
                print(f"✗ Icon '{name}' not found in catalog")
                continue

            icon = icons[0]  # Take first match
            source = ICON_DIR / icon["filename"]
            target = icon_dir / f"{icon['semanticName']}.png"

            if source.exists():
                shutil.copy2(source, target)
                exported.append(icon['semanticName'])

                # Track usage
                project_name = project.name
                if project_name not in icon.get("usedIn", []):
                    icon.setdefault("usedIn", []).append(project_name)

                print(f"✓ Exported {icon['semanticName']}.png")

        if exported:
            self.save_catalog()
            self.track_usage(project_path, exported)
            print(f"\n✓ Exported {len(exported)} icons to {icon_dir}")

    def track_usage(self, project_path: str, icon_names: List[str]):
        """Track icon usage for history and analytics"""
        project = Path(project_path).resolve()
        project_name = project.name
        timestamp = datetime.now().isoformat()

        # Update history (per-project)
        history = {}
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)

        history[project_name] = {
            "path": str(project),
            "icons": icon_names,
            "timestamp": timestamp
        }

        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)

        # Update analytics (global)
        analytics = {}
        if ANALYTICS_FILE.exists():
            with open(ANALYTICS_FILE, 'r') as f:
                analytics = json.load(f)

        for icon_name in icon_names:
            if icon_name not in analytics:
                analytics[icon_name] = {"count": 0, "projects": []}
            analytics[icon_name]["count"] += 1
            if project_name not in analytics[icon_name]["projects"]:
                analytics[icon_name]["projects"].append(project_name)

        with open(ANALYTICS_FILE, 'w') as f:
            json.dump(analytics, f, indent=2)

    def get_project_history(self, project_path: str) -> Optional[Dict]:
        """Get icon usage history for a specific project"""
        if not HISTORY_FILE.exists():
            return None

        project_name = Path(project_path).resolve().name

        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)

        return history.get(project_name)

    def get_popular_icons(self, limit: int = 10) -> List[tuple]:
        """Get most popular icons globally"""
        if not ANALYTICS_FILE.exists():
            return []

        with open(ANALYTICS_FILE, 'r') as f:
            analytics = json.load(f)

        # Sort by usage count
        sorted_icons = sorted(analytics.items(), key=lambda x: x[1]["count"], reverse=True)
        return sorted_icons[:limit]

    def show_history(self, project_path: str):
        """Show icon usage history for project"""
        history = self.get_project_history(project_path)

        if not history:
            print(f"No history found for project")
            return

        print(f"\n=== Icon Usage History ===")
        print(f"Project: {Path(project_path).name}")
        print(f"Last used: {history['timestamp']}")
        print(f"Icons: {', '.join(history['icons'])}")

    def show_popular(self, limit: int = 10):
        """Show most popular icons"""
        popular = self.get_popular_icons(limit)

        if not popular:
            print("No usage data yet")
            return

        print(f"\n=== Most Popular Icons (Top {limit}) ===\n")
        for i, (icon_name, data) in enumerate(popular, 1):
            count = data["count"]
            projects = len(data["projects"])
            print(f"{i:2}. {icon_name:20} - {count} uses across {projects} project(s)")

    def stats(self):
        """Show catalog statistics with enhanced category breakdowns"""
        total = len(self.catalog["icons"])
        by_category = {}
        category_icons = {}

        for icon in self.catalog["icons"]:
            cat = icon.get("category", "uncategorized")
            by_category[cat] = by_category.get(cat, 0) + 1
            category_icons.setdefault(cat, []).append(icon)

        # Count total icons in raw directory
        raw_total = len(list(RAW_DIR.glob("*.png"))) if RAW_DIR.exists() else 0
        uncataloged = raw_total - total
        coverage_pct = (total / raw_total * 100) if raw_total > 0 else 0

        print("\n=== Icon Library Statistics ===")
        print(f"Total icons in library: {raw_total:,}")
        print(f"Cataloged: {total} ({coverage_pct:.1f}%)")
        print(f"Uncataloged: {uncataloged:,}")

        print(f"\n=== Category Breakdown ===")
        for cat in sorted(by_category.keys()):
            count = by_category[cat]
            icons = category_icons[cat]

            # Show category with count
            print(f"\n{cat.upper()} ({count} icons):")

            # Show sample icons (first 10)
            samples = icons[:10]
            for icon in samples:
                print(f"  • {icon['semanticName']}")

            if count > 10:
                print(f"  ... and {count - 10} more")

        # Most used icons
        used_icons = [(icon, len(icon.get("usedIn", [])))
                      for icon in self.catalog["icons"]
                      if icon.get("usedIn")]
        if used_icons:
            print(f"\n=== Most Used Icons ===")
            for icon, count in sorted(used_icons, key=lambda x: x[1], reverse=True)[:5]:
                projects = ", ".join(icon["usedIn"])
                print(f"  {icon['semanticName']:15} used in {count} project(s): {projects}")

        # Project usage
        projects_using = set()
        for icon in self.catalog["icons"]:
            projects_using.update(icon.get("usedIn", []))

        if projects_using:
            print(f"\n=== Project Usage ===")
            print(f"Icons used in {len(projects_using)} project(s): {', '.join(sorted(projects_using))}")

    def bulk_import(self, csv_file: str):
        """Import icons from CSV file

        CSV Format: id,semantic,tags,category,description
        Example: Lock,lock,"security,padlock,locked",security,Padlock icon for security

        Args:
            csv_file: Path to CSV file
        """
        csv_path = Path(csv_file)
        if not csv_path.exists():
            print(f"✗ Error: CSV file not found: {csv_file}")
            return

        success_count = 0
        error_count = 0

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Validate headers
            required_headers = {'id', 'semantic', 'tags', 'category'}
            if not required_headers.issubset(reader.fieldnames):
                print(f"✗ Error: CSV must have headers: id, semantic, tags, category, description")
                print(f"  Found: {', '.join(reader.fieldnames)}")
                return

            print(f"Importing icons from {csv_file}...")

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                try:
                    # Parse tags (handle comma-separated or space-separated)
                    tags_str = row['tags'].strip()
                    if ',' in tags_str:
                        tags = [t.strip() for t in tags_str.split(',') if t.strip()]
                    else:
                        tags = [t.strip() for t in tags_str.split() if t.strip()]

                    # Validate category
                    category = row['category'].strip()
                    if category not in self.catalog["categories"]:
                        print(f"  ✗ Row {row_num}: Invalid category '{category}', skipping")
                        error_count += 1
                        continue

                    # Add icon
                    icon_id = row['id'].strip()
                    semantic = row['semantic'].strip()
                    description = row.get('description', '').strip()

                    if not icon_id or not semantic:
                        print(f"  ✗ Row {row_num}: Missing id or semantic name, skipping")
                        error_count += 1
                        continue

                    # Check if already exists
                    existing = self.find_icon_by_id(icon_id)
                    if existing:
                        print(f"  ⚠ Row {row_num}: Icon '{icon_id}' already exists, skipping")
                        continue

                    self.add_icon(icon_id, semantic, tags, category, description, save=False)
                    success_count += 1

                except Exception as e:
                    print(f"  ✗ Row {row_num}: Error processing row: {e}")
                    error_count += 1

        # Final summary and save
        if success_count > 0:
            self.save_catalog()
            
        print(f"\n=== Import Summary ===")
        print(f"✓ Successfully imported: {success_count} icons")
        if error_count > 0:
            print(f"✗ Errors/Skipped: {error_count}")
        print(f"Total cataloged icons: {len(self.catalog['icons'])}")

    def suggest_from_filename(self, filename: str) -> dict:
        """Generate semantic name and tags from filename

        Args:
            filename: Icon filename (without extension)

        Returns:
            dict with suggested semantic, tags, category
        """
        import re

        # Clean filename: lowercase, replace separators with spaces
        name = filename.replace('_', ' ').replace('-', ' ')
        name = re.sub(r'\s+', ' ', name).strip().lower()

        # Generate semantic name (lowercase with hyphens)
        semantic = name.replace(' ', '-')

        # Generate tags from words
        words = name.split()
        tags = list(set(words))  # Remove duplicates

        # Guess category based on common keywords
        category_keywords = {
            'files': ['file', 'document', 'folder', 'pdf', 'doc', 'text', 'page', 'book', 'paper'],
            'network': ['network', 'wifi', 'cloud', 'internet', 'connection', 'globe', 'web', 'server', 'router'],
            'security': ['lock', 'key', 'shield', 'security', 'secure', 'certificate', 'password', 'protection'],
            'tools': ['tool', 'wrench', 'gear', 'settings', 'config', 'hammer', 'screwdriver', 'toolbox'],
            'ui': ['button', 'icon', 'arrow', 'close', 'open', 'menu', 'navigation', 'pointer', 'cursor'],
            'development': ['code', 'bug', 'database', 'api', 'console', 'terminal', 'git', 'debug', 'test'],
            'emoji': ['smile', 'happy', 'sad', 'face', 'emotion', 'laugh', 'cry']
        }

        # Find matching category
        category = 'ui'  # Default
        max_matches = 0
        for cat, keywords in category_keywords.items():
            matches = sum(1 for word in words if any(kw in word for kw in keywords))
            if matches > max_matches:
                max_matches = matches
                category = cat

        return {
            'semantic': semantic,
            'tags': tags,
            'category': category
        }

    def generate_csv_from_filenames(self, output_file: str, limit: int = None):
        """Generate CSV file with suggestions from icon filenames

        Args:
            output_file: Path to output CSV file
            limit: Maximum number of icons to process (None = all)
        """
        print(f"Scanning {RAW_DIR} for uncataloged icons...")

        # Get all PNG files in raw directory
        all_icons = [f.stem for f in RAW_DIR.glob("*.png")]

        # Filter out already cataloged icons
        cataloged_ids = {icon['id'] for icon in self.catalog['icons']}
        uncataloged = [icon for icon in all_icons if icon not in cataloged_ids]

        if not uncataloged:
            print("✓ All icons are already cataloged!")
            return

        print(f"Found {len(uncataloged)} uncataloged icons")

        if limit:
            uncataloged = uncataloged[:limit]
            print(f"Limiting to {limit} icons for CSV generation")

        # Generate suggestions
        suggestions = []
        for icon_id in uncataloged:
            suggestion = self.suggest_from_filename(icon_id)
            suggestions.append({
                'id': icon_id,
                'semantic': suggestion['semantic'],
                'tags': ','.join(suggestion['tags'][:5]),  # Limit to 5 tags
                'category': suggestion['category'],
                'description': f"{suggestion['semantic'].replace('-', ' ').title()} icon"
            })

        # Write to CSV
        output_path = Path(output_file)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['id', 'semantic', 'tags', 'category', 'description']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(suggestions)

        print(f"\n✓ Generated {len(suggestions)} icon suggestions")
        print(f"✓ Saved to: {output_path}")
        print(f"\nNext steps:")
        print(f"1. Review and edit {output_path} in a spreadsheet")
        print(f"2. Improve tags and descriptions as needed")
        print(f"3. Import with: python3 icon-manager.py import-csv {output_path}")

    def create_template(self, template_name: str, tags: List[str], category: str):
        """Create a reusable template for icon families

        Args:
            template_name: Name of the template (e.g., 'arrow', 'social-media')
            tags: Common tags to apply
            category: Category for this icon family
        """
        # Load or create templates file
        templates_file = ICON_DIR / "icon-templates.json"
        if templates_file.exists():
            with open(templates_file, 'r') as f:
                templates = json.load(f)
        else:
            templates = {}

        templates[template_name] = {
            'tags': tags,
            'category': category
        }

        with open(templates_file, 'w') as f:
            json.dump(templates, f, indent=2)

        print(f"✓ Created template '{template_name}'")
        print(f"  Category: {category}")
        print(f"  Tags: {', '.join(tags)}")

    def apply_template(self, template_name: str, icon_specs: List[dict]):
        """Apply a template to multiple icons

        Args:
            template_name: Name of the template to apply
            icon_specs: List of dicts with 'id', 'semantic', and optional extra 'tags'
        """
        templates_file = ICON_DIR / "icon-templates.json"
        if not templates_file.exists():
            print(f"✗ No templates found. Create one with 'create-template' first")
            return

        with open(templates_file, 'r') as f:
            templates = json.load(f)

        if template_name not in templates:
            print(f"✗ Template '{template_name}' not found")
            print(f"Available templates: {', '.join(templates.keys())}")
            return

        template = templates[template_name]
        success_count = 0

        print(f"Applying template '{template_name}' to {len(icon_specs)} icons...")

        for spec in icon_specs:
            icon_id = spec['id']
            semantic = spec['semantic']
            extra_tags = spec.get('extra_tags', [])
            description = spec.get('description', f"{semantic.replace('-', ' ').title()} icon")

            # Combine template tags with any extra tags
            all_tags = template['tags'] + extra_tags

            # Check if already exists
            if self.find_icon_by_id(icon_id):
                print(f"  ⚠ '{icon_id}' already exists, skipping")
                continue

            self.add_icon(icon_id, semantic, all_tags, template['category'], description, save=False)
            success_count += 1

        if success_count > 0:
            self.save_catalog()

        print(f"\n✓ Applied template to {success_count} icons")

    def enrich_catalog(self, dry_run: bool = True) -> dict:
        """Auto-enrich icons with derived semantic tags based on their names

        Uses semantic name analysis to add missing tags for better LLM matching.

        Args:
            dry_run: If True, report changes without saving

        Returns:
            dict with stats about enrichment
        """
        # Tag derivation rules based on semantic name components
        TAG_DERIVATIONS = {
            # Security domain
            'lock': ['security', 'access', 'protected', 'authentication'],
            'key': ['security', 'access', 'credential', 'authentication'],
            'shield': ['security', 'protection', 'guard', 'defense'],
            'certificate': ['security', 'ssl', 'tls', 'credential', 'verified'],

            # Files domain
            'folder': ['directory', 'files', 'storage', 'organize'],
            'document': ['file', 'text', 'paper', 'content'],
            'file': ['document', 'content', 'data'],
            'pdf': ['document', 'file', 'adobe', 'portable'],

            # Network domain
            'network': ['connection', 'internet', 'web', 'connectivity'],
            'cloud': ['server', 'hosting', 'storage', 'online'],
            'globe': ['world', 'global', 'international', 'web'],
            'wifi': ['wireless', 'network', 'connection', 'signal'],

            # UI domain
            'arrow': ['navigation', 'direction', 'movement', 'ui'],
            'button': ['ui', 'control', 'interface', 'click'],
            'menu': ['navigation', 'ui', 'list', 'options'],
            'checkbox': ['selection', 'toggle', 'form', 'input'],

            # Status domain
            'warning': ['alert', 'caution', 'attention', 'status'],
            'error': ['fail', 'problem', 'issue', 'status'],
            'success': ['done', 'complete', 'check', 'status'],
            'info': ['information', 'help', 'about', 'notice'],

            # Tools domain
            'search': ['find', 'lookup', 'query', 'magnify'],
            'settings': ['config', 'options', 'preferences', 'gear'],
            'toolbox': ['tools', 'utilities', 'equipment', 'kit'],

            # Actions
            'download': ['save', 'fetch', 'get', 'receive'],
            'upload': ['send', 'push', 'share', 'transmit'],
            'refresh': ['reload', 'sync', 'update', 'renew'],
            'delete': ['remove', 'trash', 'erase', 'clear'],

            # Development
            'database': ['data', 'storage', 'sql', 'records'],
            'console': ['terminal', 'shell', 'command', 'cli'],
            'code': ['programming', 'script', 'source', 'dev'],

            # Media
            'camera': ['photo', 'capture', 'image', 'picture'],
            'video': ['movie', 'film', 'media', 'recording'],
            'audio': ['sound', 'music', 'speaker', 'volume'],

            # Communication
            'email': ['mail', 'message', 'inbox', 'envelope'],
            'chat': ['message', 'conversation', 'communication'],
            'phone': ['call', 'mobile', 'telephone', 'contact'],

            # Commerce
            'cart': ['shopping', 'purchase', 'buy', 'checkout'],
            'credit': ['payment', 'card', 'finance', 'transaction'],

            # Time
            'clock': ['time', 'timer', 'schedule', 'hour'],
            'calendar': ['date', 'schedule', 'event', 'planner'],
        }

        # Size tags to ignore
        size_tags = {'16x16', '24x24', '32x32', '48x48', '64x64', '72x72',
                     '80x80', '96x96', '128x128', '256x256', '12x12'}
        generic_tags = {'icon', 'generic', 'ui-element', 'numbered'}

        enriched_count = 0
        tags_added = 0
        changes = []

        for icon in self.catalog['icons']:
            semantic_name = icon['semanticName'].lower()
            current_tags = set(icon.get('tags', []))
            semantic_tags = current_tags - size_tags - generic_tags
            new_tags = set()

            # Check each derivation rule
            for keyword, derived_tags in TAG_DERIVATIONS.items():
                if keyword in semantic_name:
                    for tag in derived_tags:
                        if tag not in current_tags:
                            new_tags.add(tag)

            if new_tags:
                enriched_count += 1
                tags_added += len(new_tags)

                if dry_run:
                    changes.append({
                        'name': icon['semanticName'],
                        'current': len(semantic_tags),
                        'adding': list(new_tags)
                    })
                else:
                    icon['tags'] = list(current_tags | new_tags)

        if not dry_run and enriched_count > 0:
            self.save_catalog()

        return {
            'enriched': enriched_count,
            'tags_added': tags_added,
            'dry_run': dry_run,
            'changes': changes[:50]  # Limit output
        }

    def scan_emojis(self, project_path: str):
        """Scan a project for emoji usage and suggest icon replacements"""
        from pathlib import Path

        project = Path(project_path)
        readme_path = project / "README.md"

        if not readme_path.exists():
            readme_path = project / "readme.md"

        if not readme_path.exists():
            print(f"✗ No README.md found in {project_path}")
            return

        result = EmojiMapper.scan_readme(str(readme_path))

        if 'error' in result:
            print(f"✗ {result['error']}")
            return

        print(f"\n=== Emoji Scan Results ===")
        print(f"File: {result['file']}")
        print(f"Total emojis found: {result['total_emojis']}")
        print(f"Unique icons needed: {result['unique_icons_needed']}")

        if result['replacements']:
            print(f"\n=== Replacement Suggestions ===\n")
            for icon_name, data in sorted(result['replacements'].items()):
                print(f"  {data['emoji']} → {icon_name} ({data['count']} occurrences)")
                for ctx in data['contexts'][:2]:
                    print(f"      {ctx[:60]}...")

            # Show export command
            icons_needed = list(result['replacements'].keys())
            print(f"\n=== Quick Export ===")
            print(f"icon use {' '.join(icons_needed[:10])}")
        else:
            print("\nNo recognized emojis found!")

    def validate(self):
        """Validate catalog integrity - check for missing files, broken symlinks, etc."""
        print("\n=== Validating Icon Catalog ===\n")

        issues = []
        warnings = []

        # Check if required directories exist
        if not RAW_DIR.exists():
            issues.append(f"✗ RAW directory missing: {RAW_DIR}")
        if not CATALOG_DIR.exists():
            issues.append(f"✗ CATALOG directory missing: {CATALOG_DIR}")

        # Check each icon in catalog
        for icon in self.catalog["icons"]:
            icon_id = icon['id']
            semantic = icon['semanticName']
            filename = icon.get('filename', f"raw/{icon_id}.png")

            # Check if source file exists
            source_path = ICON_DIR / filename
            if not source_path.exists():
                issues.append(f"✗ Missing source file for '{semantic}' (#{icon_id}): {filename}")

            # Check if symlink exists in catalog
            category = icon.get('category', 'uncategorized')
            symlink_path = CATALOG_DIR / category / f"{semantic}.png"
            if not symlink_path.exists():
                warnings.append(f"⚠ Missing catalog symlink for '{semantic}' at: {symlink_path}")
            elif not symlink_path.is_symlink():
                warnings.append(f"⚠ Not a symlink: {symlink_path}")

        # Check for orphaned symlinks (symlinks pointing to non-existent files)
        if CATALOG_DIR.exists():
            for category_dir in CATALOG_DIR.iterdir():
                if category_dir.is_dir():
                    for symlink in category_dir.glob("*.png"):
                        if symlink.is_symlink():
                            target = symlink.resolve()
                            if not target.exists():
                                issues.append(f"✗ Broken symlink: {symlink} → {target}")

        # Report results
        if not issues and not warnings:
            print("✓ Catalog validation passed! No issues found.")
        else:
            if issues:
                print(f"Found {len(issues)} issue(s):")
                for issue in issues:
                    print(f"  {issue}")
            if warnings:
                print(f"\nFound {len(warnings)} warning(s):")
                for warning in warnings:
                    print(f"  {warning}")

        print(f"\nSummary:")
        print(f"  Total icons in catalog: {len(self.catalog['icons'])}")
        print(f"  Issues: {len(issues)}")
        print(f"  Warnings: {len(warnings)}")

    def info(self, semantic_name: str):
        """Show detailed information about a specific icon"""
        icons = self.find_icons_by_semantic(semantic_name)

        if not icons:
            print(f"✗ Icon '{semantic_name}' not found")
            return

        icon = icons[0]

        print(f"\n=== Icon Information ===")
        print(f"Semantic Name: {icon['semanticName']}")
        print(f"Icon ID: #{icon['id']}")
        print(f"Filename: {icon.get('filename', 'N/A')}")
        print(f"Category: {icon.get('category', 'uncategorized')}")
        print(f"Description: {icon.get('description', 'No description')}")

        tags = icon.get('tags', [])
        print(f"Tags: {', '.join(tags) if tags else 'none'}")

        used_in = icon.get('usedIn', [])
        if used_in:
            print(f"Used in projects: {', '.join(used_in)}")
        else:
            print(f"Used in projects: none")

        # Check if files exist
        source_path = ICON_DIR / icon.get('filename', f"raw/{icon['id']}.png")
        symlink_path = CATALOG_DIR / icon.get('category', 'uncategorized') / f"{icon['semanticName']}.png"

        print(f"\nFile Status:")
        print(f"  Source: {'✓ exists' if source_path.exists() else '✗ missing'} ({source_path})")
        print(f"  Symlink: {'✓ exists' if symlink_path.exists() else '✗ missing'} ({symlink_path})")

    def recent(self, limit: int = 20):
        """Show recently cataloged icons (last N additions)"""
        icons = self.catalog["icons"]

        if not icons:
            print("No icons in catalog")
            return

        # Icons are appended to the list, so last ones are most recent
        recent_icons = icons[-limit:] if len(icons) > limit else icons
        recent_icons.reverse()  # Show newest first

        print(f"\n=== Recently Cataloged Icons (last {len(recent_icons)}) ===\n")

        for icon in recent_icons:
            tags = ", ".join(icon.get('tags', [])[:5])  # Show first 5 tags
            if len(icon.get('tags', [])) > 5:
                tags += ", ..."
            print(f"  {icon['semanticName']:20} #{icon['id']:4}  [{icon['category']:12}]  {tags}")

    def export_category(self, project_path: str, category: str):
        """Export all icons from a specific category to a project"""
        if category not in self.catalog["categories"]:
            print(f"✗ Invalid category: {category}")
            print(f"Available categories: {', '.join(self.catalog['categories'])}")
            return

        # Find all icons in this category
        category_icons = [icon for icon in self.catalog["icons"]
                         if icon.get("category") == category]

        if not category_icons:
            print(f"No icons found in category '{category}'")
            return

        print(f"Found {len(category_icons)} icons in '{category}' category")

        # Export them
        icon_names = [icon['semanticName'] for icon in category_icons]
        self.export_to_project(project_path, icon_names)

    def standardize_library(self, limit: Optional[int] = None, dry_run: bool = True):
        """Standardize all filenames and metadata in the library"""
        print(f"Standardizing library (Limit: {limit}, Dry Run: {dry_run})...")
        
        changes = []
        id_map = {} # old_id -> new_id
        
        processed_count = 0
        for icon in self.catalog["icons"]:
            if limit and processed_count >= limit:
                break
                
            old_id = icon["id"]
            old_semantic = icon["semanticName"]
            
            # Standard naming: lowercase, alphanumeric + hyphens
            new_semantic = re.sub(r'[^a-z0-9]+', '-', old_semantic.lower()).strip('-')
            
            # Ensure size is in semantic name if not present
            source_path = RAW_DIR / f"{old_id}.png"
            size_str = ""
            if source_path.exists():
                try:
                    with Image.open(source_path) as img:
                        w, h = img.size
                        size_str = f"{w}x{h}"
                        if size_str not in new_semantic:
                            new_semantic = f"{new_semantic}-{size_str}"
                except Exception:
                    pass
            
            new_id = new_semantic
            id_map[old_id] = new_id
            
            if old_id != new_id or old_semantic != new_semantic:
                changes.append({
                    "old_id": old_id,
                    "new_id": new_id,
                    "old_semantic": old_semantic,
                    "new_semantic": new_semantic,
                    "old_file": f"raw/{old_id}.png",
                    "new_file": f"raw/{new_id}.png"
                })
            
            processed_count += 1

        if not changes:
            print("✓ Library is already standardized!")
            return

        print(f"Found {len(changes)} icons to standardize.")
        
        if dry_run:
            for change in changes[:10]:
                print(f"  [PREVIEW] {change['old_id']} -> {change['new_id']}")
            if len(changes) > 10:
                print(f"  ... and {len(changes) - 10} more")
            return

        # 2. Apply changes
        success_count = 0
        for change in changes:
            old_path = ICON_DIR / change["old_file"]
            new_path = ICON_DIR / change["new_file"]
            
            # Rename file
            if old_path.exists():
                if new_path.exists() and old_path != new_path:
                    # Collision! This is a deduplication opportunity
                    print(f"  ⚠ Collision: {change['new_id']} already exists. Skipping rename.")
                else:
                    try:
                        old_path.rename(new_path)
                    except Exception as e:
                        print(f"  ✗ Error renaming {change['old_id']}: {e}")
                        continue
            
            # Update catalog entry
            icon = self.find_icon_by_id(change["old_id"])
            if icon:
                icon["id"] = change["new_id"]
                icon["semanticName"] = change["new_semantic"]
                icon["filename"] = change["new_file"]
                success_count += 1

        if success_count > 0:
            self.save_catalog()
            # Clean and recreate symlinks
            shutil.rmtree(CATALOG_DIR, ignore_errors=True)
            for icon in self.catalog["icons"]:
                self.create_symlink(icon["id"], icon["semanticName"], icon["category"])
            
        print(f"✓ Standardized {success_count} icons.")

    def deduplicate(self, dry_run: bool = True):
        """Find and remove duplicate icons based on visual content (hash)"""
        import hashlib
        
        print(f"Deduplicating library (Dry Run: {dry_run})...")
        hashes = {} # hash -> [icon_ids]
        
        for icon in self.catalog["icons"]:
            path = ICON_DIR / icon["filename"]
            if not path.exists(): continue
            
            with open(path, "rb") as f:
                img_hash = hashlib.md5(f.read()).hexdigest()
                
            if img_hash not in hashes: hashes[img_hash] = []
            hashes[img_hash].append(icon["id"])
            
        duplicates_found = 0
        removed_count = 0
        
        for img_hash, ids in hashes.items():
            if len(ids) > 1:
                duplicates_found += 1
                # Keep the one with the best name (shortest or most semantic)
                ids.sort(key=lambda x: (len(x), x))
                keep_id = ids[0]
                remove_ids = ids[1:]
                
                if dry_run:
                    print(f"  [PREVIEW] Duplicates of {keep_id}: {', '.join(remove_ids)}")
                else:
                    # Update usage tracking for the kept icon if needed
                    keep_icon = self.find_icon_by_id(keep_id)
                    for rid in remove_ids:
                        remove_icon = self.find_icon_by_id(rid)
                        if remove_icon and "usedIn" in remove_icon:
                            for proj in remove_icon["usedIn"]:
                                if proj not in keep_icon.get("usedIn", []):
                                    keep_icon.setdefault("usedIn", []).append(proj)
                        
                        # Remove from catalog
                        self.catalog["icons"] = [icon for icon in self.catalog["icons"] if icon["id"] != rid]
                        # Remove file
                        remove_path = ICON_DIR / f"raw/{rid}.png"
                        if remove_path.exists(): remove_path.unlink()
                        removed_count += 1

        if not dry_run and removed_count > 0:
            self.save_catalog()
            print(f"✓ Removed {removed_count} duplicate icons.")
        elif duplicates_found == 0:
            print("✓ No duplicates found.")

    def generate_gallery(self, output_file: str = "gallery.html"):
        """Generate a visual HTML gallery"""
        output_path = ICON_DIR / output_file
        if GalleryGenerator.generate(self.catalog, output_path):
            print(f"✓ Gallery generated at {output_path}")

    def llm_enrich(self, limit: int = 100, dry_run: bool = True, verify: bool = False):
        """Enrichment 2.1: Apply Schema 2.1 with Tag Grounding and Confidence"""
        print(f"Enriching up to {limit} icons (Schema 2.1, Verify: {verify}, Dry Run: {dry_run})...")
        
        # Negative mapping for tag grounding: metaphor -> forbidden keywords in tags
        TAG_GROUNDING_CONSTRAINTS = {
            "risk": ["tool", "utility", "fix", "repair", "service"],
            "security": ["time", "clock", "watch"],
            "communication": ["capture", "camera", "photo"],
            "failure": ["check", "tick", "success", "done"]
        }
        
        KNOWLEDGE_BASE = {
            "lock": ("security", 0.0, 3, "Authentication, privacy, restriction"),
            "shield": ("protection", 0.5, 3, "Safety, data guard, firewall"),
            "database": ("storage", -0.1, 2, "Data persistence, backend, records"),
            "cloud": ("connectivity", 0.2, 4, "Remote sync, SaaS, online services"),
            "terminal": ("automation", -0.2, 4, "CLI, dev tools, system execution"),
            "gear": ("configuration", 0.0, 3, "Settings, preferences, engine control"),
            "search": ("discovery", 0.3, 3, "Query, lookup, finding content"),
            "warning": ("risk", -0.6, 4, "Error prevention, attention, data loss"),
            "error": ("failure", -1.0, 5, "System crash, invalid input, critical stop"),
            "success": ("completion", 1.0, 5, "Task done, verified, positive feedback"),
            "document": ("information", 0.0, 1, "File management, reports, text"),
            "user": ("identity", 0.4, 2, "Profiles, members, account settings"),
            "email": ("communication", 0.1, 2, "Contact, messaging, notifications"),
            "camera": ("capture", 0.2, 1, "Multimedia, image upload, vision"),
            "folder": ("organization", 0.0, 2, "Directory structure, grouping"),
            "star": ("favorite", 0.9, 4, "Rating, bookmarking, highlighted"),
            "heart": ("appreciation", 1.0, 5, "Social likes, love, favorites"),
            "trash": ("disposal", -0.4, 3, "Delete, clear, remove content"),
            "edit": ("modification", 0.1, 3, "Pencil, change, write"),
            "add": ("creation", 0.6, 4, "Plus, insert, new item")
        }
        
        modified_count = 0
        verification_data = []
        
        for icon in self.catalog["icons"]:
            if modified_count >= limit: break
            
            # Find all high-quality semantic matches
            scored_matches = []
            for concept, data in KNOWLEDGE_BASE.items():
                score = SemanticMatcher.calculate_match_score(icon, concept)
                if score >= 0.85:
                    scored_matches.append((concept, score, data))
            
            if not scored_matches:
                continue
                
            # Sort to find winner and runner-up
            scored_matches.sort(key=lambda x: -x[1])
            best_concept, best_score, (metaphor, valence, abstraction, use_cases) = scored_matches[0]
            runner_up_score = scored_matches[1][1] if len(scored_matches) > 1 else 0
            
            # --- TAG GROUNDING CHECK ---
            tags = [t.lower() for t in icon.get("tags", [])]
            forbidden = TAG_GROUNDING_CONSTRAINTS.get(metaphor, [])
            # Precise list check: ensures forbidden words are not present in the tags
            if any(f in tags for f in forbidden):
                continue
            
            # Check if already enriched with this specific metaphor
            if icon.get("metaphor") == metaphor:
                continue
            
            # --- ADVANCED CONFIDENCE CALCULATION ---
            # 1. Ambiguity Penalty: If two concepts are very close, confidence drops
            ambiguity_penalty = max(0, 1 - (best_score - runner_up_score) * 2)
            
            # 2. Tag Alignment: Bonus if tags overlap with the intended use-cases/description
            # Normalize use_cases to set of words
            use_case_words = set(re.sub(r'[^a-z]+', ' ', use_cases.lower()).split())
            tag_alignment = len(set(tags) & use_case_words) / max(len(tags), 1)
            
            # 3. Aggregate Confidence: Score * machine-discount * ambiguity * alignment
            # Base discount: 0.95 (machine generated)
            # Alignment factor: 0.7 base + up to 0.3 bonus
            confidence = round(
                best_score * 0.95 * 
                (1 - ambiguity_penalty * 0.3) * 
                (0.7 + tag_alignment * 0.3), 
                2
            )
            
            if verify:
                verification_data.append({
                    'id': icon['id'],
                    'name': icon['semanticName'],
                    'concept': best_concept,
                    'score': f"{best_score:.2f}",
                    'metaphor': metaphor,
                    'confidence': confidence,
                    'alignment': f"{tag_alignment:.2f}"
                })
                modified_count += 1
                continue

            if not dry_run:
                icon["metaphor"] = metaphor
                icon["emotional_valence"] = valence
                icon["abstraction_level"] = abstraction
                icon["enrichment_confidence"] = confidence
                
                # Update description if use cases not present
                current_desc = icon.get('description', '')
                use_case_str = f"Use cases: {use_cases}"
                if use_case_str not in current_desc:
                     icon["description"] = f"{current_desc}. {use_case_str}".strip(". ") + "."
            else:
                print(f"  [PREVIEW] {icon['semanticName']} -> {metaphor} (Conf: {confidence}, Align: {tag_alignment:.2f})")
            
            modified_count += 1

        if verify and verification_data:
            verify_file = ICON_DIR / "enrichment_verification_v2.1.csv"
            with open(verify_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'name', 'concept', 'score', 'metaphor', 'confidence', 'alignment'])
                writer.writeheader()
                writer.writerows(verification_data)
            print(f"✓ Verification sample exported to {verify_file}")
            return

        if not dry_run and modified_count > 0:
            self.save_catalog()
            
        print(f"✓ Processed library, applied {modified_count} new Schema 2.1 enrichments.")

def main():
    parser = argparse.ArgumentParser(description="Icon library management system")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add icon to catalog")
    add_parser.add_argument("icon_id", help="Numeric icon ID (e.g., 100)")
    add_parser.add_argument("semantic_name", help="Semantic name (e.g., document)")
    add_parser.add_argument("--tags", nargs="+", required=True, help="Tags (e.g., file text document)")
    add_parser.add_argument("--category", required=True, choices=["files", "network", "security", "tools", "ui", "emoji", "development"])
    add_parser.add_argument("--description", default="", help="Description")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search icons")
    search_parser.add_argument("query", help="Search query (tag or semantic name)")

    # List command
    list_parser = subparsers.add_parser("list", help="List icons in category")
    list_parser.add_argument("category", choices=["files", "network", "security", "tools", "ui", "emoji", "development"])

    # Export command
    export_parser = subparsers.add_parser("export", help="Export icons to project")
    export_parser.add_argument("project_path", help="Path to project directory")
    export_parser.add_argument("icons", nargs="+", help="Icon semantic names to export")

    # Stats command
    subparsers.add_parser("stats", help="Show catalog statistics")

    # Import CSV command
    import_parser = subparsers.add_parser("import-csv", help="Bulk import icons from CSV file")
    import_parser.add_argument("csv_file", help="Path to CSV file (id,semantic,tags,category,description)")

    # Generate CSV command
    generate_parser = subparsers.add_parser("generate-csv", help="Auto-generate CSV from uncataloged icon filenames")
    generate_parser.add_argument("output_file", help="Path to output CSV file")
    generate_parser.add_argument("--limit", type=int, help="Maximum number of icons to process (default: all)")

    # Template commands
    template_create_parser = subparsers.add_parser("create-template", help="Create reusable template for icon families")
    template_create_parser.add_argument("name", help="Template name (e.g., arrow, social)")
    template_create_parser.add_argument("--tags", nargs="+", required=True, help="Common tags for this template")
    template_create_parser.add_argument("--category", required=True, choices=["files", "network", "security", "tools", "ui", "emoji", "development"])

    template_apply_parser = subparsers.add_parser("apply-template", help="Apply template to multiple icons via CSV")
    template_apply_parser.add_argument("template", help="Template name to apply")
    template_apply_parser.add_argument("csv_file", help="CSV file with id,semantic,extra_tags,description columns")

    # Validate command
    subparsers.add_parser("validate", help="Validate catalog integrity (check for missing files, broken symlinks)")

    # Info command
    info_parser = subparsers.add_parser("info", help="Show detailed information about a specific icon")
    info_parser.add_argument("semantic_name", help="Semantic name of the icon")

    # Recent command
    recent_parser = subparsers.add_parser("recent", help="Show recently cataloged icons")
    recent_parser.add_argument("--limit", type=int, default=20, help="Number of recent icons to show (default: 20)")

    # Export-category command
    export_cat_parser = subparsers.add_parser("export-category", help="Export all icons from a category to a project")
    export_cat_parser.add_argument("project_path", help="Path to project directory")
    export_cat_parser.add_argument("category", choices=["files", "network", "security", "tools", "ui", "emoji", "development"])

    # History command
    history_parser = subparsers.add_parser("history", help="Show icon usage history for project")
    history_parser.add_argument("project_path", help="Path to project directory")

    # Popular command
    popular_parser = subparsers.add_parser("popular", help="Show most popular icons")
    popular_parser.add_argument("--limit", type=int, default=10, help="Number of popular icons to show (default: 10)")

    # Suggest command (with percentage scores)
    suggest_parser = subparsers.add_parser("suggest", help="Get icon suggestions with match percentages")
    suggest_parser.add_argument("context", help="Context/topic to suggest icons for (e.g., security, authentication)")
    suggest_parser.add_argument("--limit", type=int, default=10, help="Number of suggestions to show (default: 10)")

    # Enrich command - auto-add semantic tags
    enrich_parser = subparsers.add_parser("enrich", help="Auto-enrich catalog with derived semantic tags")
    enrich_parser.add_argument("--apply", action="store_true", help="Apply changes (default: dry-run preview)")
    enrich_parser.add_argument("--verbose", action="store_true", help="Show detailed changes")

    # Scan-emojis command - find emojis in project READMEs
    scan_parser = subparsers.add_parser("scan-emojis", help="Scan project README for emoji replacements")
    scan_parser.add_argument("project_path", help="Path to project directory")

    # Standardize command
    standardize_parser = subparsers.add_parser("standardize", help="Standardize filenames and metadata")
    standardize_parser.add_argument("--limit", type=int, help="Max icons to standardize")
    standardize_parser.add_argument("--apply", action="store_true", help="Apply changes (default: dry-run)")

    # Deduplicate command
    dedupe_parser = subparsers.add_parser("dedupe", help="Remove duplicate icons based on visual content")
    dedupe_parser.add_argument("--apply", action="store_true", help="Apply changes (default: dry-run)")

    # Gallery command
    gallery_parser = subparsers.add_parser("gallery", help="Generate a visual HTML gallery")
    gallery_parser.add_argument("--output", default="gallery.html", help="Output filename")

    # LLM Enrich command
    llm_enrich_parser = subparsers.add_parser("enrich-llm", help="Enrich metadata with LLM-grade descriptions")
    llm_enrich_parser.add_argument("--limit", type=int, default=100, help="Max icons to enrich")
    llm_enrich_parser.add_argument("--apply", action="store_true", help="Apply changes (default: dry-run)")
    llm_enrich_parser.add_argument("--verify", action="store_true", help="Export a sample for verification instead of applying")

    # =========================================================================
    # CLIP Vector Subspace Commands
    # =========================================================================

    # Embed command - Generate CLIP embeddings
    embed_parser = subparsers.add_parser("embed", help="Generate CLIP embeddings for all icons")
    embed_parser.add_argument("--model", default="ViT-B-32", help="CLIP model architecture (default: ViT-B-32)")
    embed_parser.add_argument("--batch-size", type=int, default=64, help="Batch size for embedding (default: 64)")
    embed_parser.add_argument("--force", action="store_true", help="Regenerate embeddings even if they exist")
    embed_parser.add_argument("--output", choices=["table", "json"], default="table", help="Output format (default: table)")

    # Analyze-subspace command - Run SVD analysis
    analyze_parser = subparsers.add_parser("analyze-subspace", help="Run SVD analysis on icon embeddings")
    analyze_parser.add_argument("--components", type=int, default=50, help="Max components to analyze (default: 50)")
    analyze_parser.add_argument("--threshold", type=float, default=0.95, help="Variance threshold for dim selection (default: 0.95)")
    analyze_parser.add_argument("--output", choices=["table", "json"], default="table", help="Output format (default: table)")

    # Query command - Semantic icon query
    query_parser = subparsers.add_parser("query", help="Semantic search using CLIP embeddings")
    query_parser.add_argument("text", help="Text query (e.g., 'security lock protection')")
    query_parser.add_argument("--k", type=int, default=10, help="Number of results (default: 10)")
    query_parser.add_argument("--mode", choices=["raw", "projected", "weighted"], default="projected",
                              help="Retrieval mode: raw (CLIP space), projected (subspace), weighted (PC-weighted)")
    query_parser.add_argument("--output", choices=["table", "json"], default="table", help="Output format (default: table)")

    # Traverse command - Traverse semantic axis
    traverse_parser = subparsers.add_parser("traverse", help="Traverse semantic axis from an icon")
    traverse_parser.add_argument("icon_id", help="Starting icon ID (e.g., lock-32x32)")
    traverse_parser.add_argument("--axis", type=int, default=0, help="Principal component index to traverse (default: 0)")
    traverse_parser.add_argument("--steps", type=int, default=5, help="Number of steps in each direction (default: 5)")
    traverse_parser.add_argument("--direction", choices=["positive", "negative", "both"], default="both",
                                 help="Direction to traverse (default: both)")
    traverse_parser.add_argument("--output", choices=["table", "json"], default="table", help="Output format (default: table)")

    # Interpolate command - Find icons between two icons
    interpolate_parser = subparsers.add_parser("interpolate", help="Find icons along interpolation path between two icons")
    interpolate_parser.add_argument("icon_a", help="Starting icon ID")
    interpolate_parser.add_argument("icon_b", help="Ending icon ID")
    interpolate_parser.add_argument("--steps", type=int, default=5, help="Number of interpolation points (default: 5)")
    interpolate_parser.add_argument("--output", choices=["table", "json"], default="table", help="Output format (default: table)")

    # Eval-retrieval command - Evaluate retrieval quality
    eval_parser = subparsers.add_parser("eval-retrieval", help="Evaluate retrieval quality against ground truth")
    eval_parser.add_argument("--ground-truth", required=True, help="Path to ground truth JSON file")
    eval_parser.add_argument("--k", type=int, default=10, help="Cutoff for metrics (default: 10)")
    eval_parser.add_argument("--output", choices=["table", "json"], default="table", help="Output format (default: table)")

    # Residual command - Check query coverage
    residual_parser = subparsers.add_parser("residual", help="Compute orthogonal residual score for query")
    residual_parser.add_argument("text", help="Text query to analyze")
    residual_parser.add_argument("--output", choices=["table", "json"], default="table", help="Output format (default: table)")

    # =========================================================================
    # LLM Integration Commands (Phase 7)
    # =========================================================================

    # Batch query command
    batch_query_parser = subparsers.add_parser("batch-query", help="Batch semantic search for multiple queries")
    batch_query_parser.add_argument("--queries", required=True, help="Comma-separated list of queries (e.g., 'security,files,settings')")
    batch_query_parser.add_argument("--k", type=int, default=2, help="Number of results per query (default: 2)")
    batch_query_parser.add_argument("--mode", choices=["raw", "projected", "weighted"], default="projected",
                                    help="Retrieval mode (default: projected)")
    batch_query_parser.add_argument("--output", choices=["table", "json"], default="table", help="Output format (default: table)")

    # Provision command
    provision_parser = subparsers.add_parser("provision", help="Provision icons to a project directory")
    provision_parser.add_argument("--icons", help="Comma-separated list of icon IDs to provision")
    provision_parser.add_argument("--query", help="Semantic query to find icons to provision")
    provision_parser.add_argument("--manifest", help="Path to existing manifest to replicate")
    provision_parser.add_argument("--dest", required=True, help="Destination directory for icons")
    provision_parser.add_argument("--subdir", default="", help="Subdirectory within dest for icons (e.g., '.github/assets/icons')")
    provision_parser.add_argument("--k", type=int, default=2, help="Number of icons per query (used with --query)")
    provision_parser.add_argument("--output", choices=["table", "json"], default="table", help="Output format (default: table)")

    # Scan emoji command
    scan_emoji_parser = subparsers.add_parser("scan-emoji", help="Scan files for emoji usage")
    scan_emoji_parser.add_argument("--path", required=True, help="File or directory path to scan")
    scan_emoji_parser.add_argument("--extensions", default="md,mdx,tsx,jsx,html", help="Comma-separated file extensions (default: md,mdx,tsx,jsx,html)")
    scan_emoji_parser.add_argument("--recursive", action="store_true", default=True, help="Scan directories recursively")
    scan_emoji_parser.add_argument("--output", help="Output file path for JSON report (optional)")

    # Convert emoji command
    convert_emoji_parser = subparsers.add_parser("convert-emoji", help="Convert emojis to icons in files")
    convert_emoji_parser.add_argument("--report", required=True, help="Path to emoji scan report JSON")
    convert_emoji_parser.add_argument("--icon-path", default="icons", help="Icon path for markdown (default: icons)")
    convert_emoji_parser.add_argument("--dry-run", action="store_true", default=True, help="Preview changes without applying")
    convert_emoji_parser.add_argument("--apply", action="store_true", help="Apply changes (overrides --dry-run)")
    convert_emoji_parser.add_argument("--output", choices=["table", "json"], default="table", help="Output format (default: table)")

    # Generate imports command
    gen_imports_parser = subparsers.add_parser("generate-imports", help="Generate framework-specific import file")
    gen_imports_parser.add_argument("--manifest", required=True, help="Path to iconics-manifest.json")
    gen_imports_parser.add_argument("--format", required=True, choices=["react", "vue", "css", "typescript"],
                                    help="Target format")
    gen_imports_parser.add_argument("--output", required=True, help="Output file path")

    args = parser.parse_args()
    manager = IconManager()

    if args.command == "add":
        manager.add_icon(args.icon_id, args.semantic_name, args.tags,
                        args.category, args.description)

    elif args.command == "search":
        results = manager.search(args.query)
        if results:
            print(f"\nFound {len(results)} icon(s) matching '{args.query}':")
            for icon in results:
                tags = ", ".join(icon.get("tags", []))
                print(f"  {icon['semanticName']:20} #{icon['id']:4}  [{icon['category']}]  Tags: {tags}")
        else:
            print(f"No icons found matching '{args.query}'")

    elif args.command == "list":
        manager.list_category(args.category)

    elif args.command == "export":
        manager.export_to_project(args.project_path, args.icons)

    elif args.command == "stats":
        manager.stats()

    elif args.command == "import-csv":
        manager.bulk_import(args.csv_file)

    elif args.command == "generate-csv":
        manager.generate_csv_from_filenames(args.output_file, args.limit)

    elif args.command == "create-template":
        manager.create_template(args.name, args.tags, args.category)

    elif args.command == "apply-template":
        # Load CSV and apply template
        icon_specs = []
        with open(args.csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                spec = {
                    'id': row['id'],
                    'semantic': row['semantic'],
                }
                if 'extra_tags' in row and row['extra_tags']:
                    spec['extra_tags'] = [t.strip() for t in row['extra_tags'].split(',')]
                else:
                    spec['extra_tags'] = []
                if 'description' in row:
                    spec['description'] = row['description']
                icon_specs.append(spec)
        manager.apply_template(args.template, icon_specs)

    elif args.command == "validate":
        manager.validate()

    elif args.command == "info":
        manager.info(args.semantic_name)

    elif args.command == "recent":
        manager.recent(args.limit)

    elif args.command == "export-category":
        manager.export_category(args.project_path, args.category)

    elif args.command == "history":
        manager.show_history(args.project_path)

    elif args.command == "popular":
        manager.show_popular(args.limit)

    elif args.command == "suggest":
        print(manager.suggest_formatted(args.context, args.limit))

    elif args.command == "enrich":
        dry_run = not args.apply
        result = manager.enrich_catalog(dry_run=dry_run)

        print(f"\n=== Catalog Enrichment {'(DRY RUN)' if dry_run else 'APPLIED'} ===")
        print(f"Icons enriched: {result['enriched']}")
        print(f"Tags added: {result['tags_added']}")

        if args.verbose and result['changes']:
            print(f"\n=== Sample Changes ===")
            for change in result['changes'][:25]:
                tags_str = ', '.join(change['adding'])
                print(f"  {change['name']}: +{len(change['adding'])} tags ({tags_str})")

        if dry_run and result['enriched'] > 0:
            print(f"\nTo apply changes: python3 icon-manager.py enrich --apply")

    elif args.command == "scan-emojis":
        manager.scan_emojis(args.project_path)

    elif args.command == "standardize":
        manager.standardize_library(limit=args.limit, dry_run=not args.apply)

    elif args.command == "dedupe":
        manager.deduplicate(dry_run=not args.apply)

    elif args.command == "gallery":
        manager.generate_gallery(args.output)

    elif args.command == "enrich-llm":
        manager.llm_enrich(limit=args.limit, dry_run=not args.apply, verify=args.verify)

    # =========================================================================
    # CLIP Vector Subspace Command Handlers
    # =========================================================================

    elif args.command == "embed":
        # Generate CLIP embeddings for all icons
        import sys
        sys.path.insert(0, str(ICON_DIR / "src"))

        embeddings_dir = ICON_DIR / "embeddings"

        # Check if embeddings exist and not forcing regeneration
        if not args.force and (embeddings_dir / "icon_embeddings.npy").exists():
            if args.output == "json":
                import json as json_mod
                print(json_mod.dumps({
                    "status": "skipped",
                    "message": "Embeddings already exist. Use --force to regenerate.",
                    "path": str(embeddings_dir)
                }, indent=2))
            else:
                print(f"Embeddings already exist at {embeddings_dir}")
                print("Use --force to regenerate.")
            sys.exit(0)

        try:
            from iconics_embeddings import load_clip_model, embed_icons, save_embeddings

            # Get all icon paths from raw directory
            icon_paths = sorted(RAW_DIR.glob("*.png"))

            if not icon_paths:
                print("Error: No PNG files found in raw directory")
                sys.exit(1)

            print(f"Loading CLIP model: {args.model}")
            model, preprocess, tokenizer = load_clip_model(model_name=args.model)

            print(f"Embedding {len(icon_paths)} icons (batch size: {args.batch_size})...")
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            embeddings, index = embed_icons(icon_paths, model, preprocess, batch_size=args.batch_size, device=device)

            # Save embeddings
            metadata = {
                "model": args.model,
                "pretrained": "laion2b_s34b_b79k",
                "device": device,
            }
            save_embeddings(embeddings, index, embeddings_dir, metadata)

            if args.output == "json":
                import json as json_mod
                print(json_mod.dumps({
                    "status": "success",
                    "count": len(index),
                    "dimension": embeddings.shape[1],
                    "model": args.model,
                    "path": str(embeddings_dir)
                }, indent=2))
            else:
                print(f"\nEmbeddings generated successfully!")
                print(f"  Count: {len(index)}")
                print(f"  Dimension: {embeddings.shape[1]}")
                print(f"  Model: {args.model}")
                print(f"  Saved to: {embeddings_dir}")

        except ImportError as e:
            print(f"Error: Missing dependency - {e}")
            print("Install with: pip install open_clip_torch torch")
            sys.exit(1)

    elif args.command == "analyze-subspace":
        # Run SVD analysis on embeddings
        import sys
        sys.path.insert(0, str(ICON_DIR / "src"))

        embeddings_dir = ICON_DIR / "embeddings"
        subspace_dir = embeddings_dir / "subspace"

        if not (embeddings_dir / "icon_embeddings.npy").exists():
            print("Error: Embeddings not found. Run 'embed' command first.")
            sys.exit(1)

        try:
            from iconics_subspace import compute_and_save_subspace

            print(f"Running SVD analysis (threshold: {args.threshold})...")
            analysis = compute_and_save_subspace(
                embeddings_dir / "icon_embeddings.npy",
                embeddings_dir / "icon_index.json",
                subspace_dir,
                variance_threshold=args.threshold
            )

            if args.output == "json":
                import json as json_mod
                result = {
                    "effective_dim": analysis.effective_dim,
                    "total_variance": analysis.total_variance,
                    "explained_variance_ratio": analysis.explained_variance_ratio,
                    "variance_threshold": analysis.variance_threshold,
                    "elbow_point": analysis.elbow_point,
                    "path": str(subspace_dir)
                }
                print(json_mod.dumps(result, indent=2))
            else:
                print(f"\nSubspace Analysis Complete!")
                print(f"  Effective dimension: {analysis.effective_dim}")
                print(f"  Explained variance: {analysis.explained_variance_ratio:.4f}")
                print(f"  Elbow point: {analysis.elbow_point}")
                print(f"  Saved to: {subspace_dir}")

        except ImportError as e:
            print(f"Error: Missing dependency - {e}")
            print("Install required packages: pip install numpy")
            sys.exit(1)

    elif args.command == "query":
        # Semantic icon query using CLIP
        import sys
        sys.path.insert(0, str(ICON_DIR / "src"))

        embeddings_dir = ICON_DIR / "embeddings"
        subspace_dir = embeddings_dir / "subspace"

        if not (embeddings_dir / "icon_embeddings.npy").exists():
            print("Error: Embeddings not found. Run 'embed' command first.")
            sys.exit(1)

        if not (subspace_dir / "basis_vectors.npy").exists():
            print("Error: Subspace not found. Run 'analyze-subspace' command first.")
            sys.exit(1)

        try:
            from iconics_retrieval import IconicsRetriever

            retriever = IconicsRetriever(
                embeddings_path=str(embeddings_dir),
                subspace_path=str(subspace_dir)
            )

            results = retriever.retrieve(args.text, k=args.k, mode=args.mode)
            residual = results[0].residual_score if results else 0.0

            if args.output == "json":
                import json as json_mod
                output = {
                    "query": args.text,
                    "mode": args.mode,
                    "residual_score": residual,
                    "results": [
                        {"rank": i+1, "icon_id": r.icon_id, "score": r.score}
                        for i, r in enumerate(results)
                    ]
                }
                print(json_mod.dumps(output, indent=2))
            else:
                print(f"\nQuery: {args.text}")
                print(f"Mode: {args.mode}")
                print(f"Residual Score: {residual:.4f}")
                print()
                print(f"| {'Rank':^4} | {'Icon ID':<30} | {'Score':^8} |")
                print(f"|{'-'*6}|{'-'*32}|{'-'*10}|")
                for i, r in enumerate(results):
                    print(f"| {i+1:^4} | {r.icon_id:<30} | {r.score:>8.4f} |")

        except ImportError as e:
            print(f"Error: Missing dependency - {e}")
            print("Install required packages: pip install faiss-cpu open_clip_torch torch")
            sys.exit(1)

    elif args.command == "traverse":
        # Traverse semantic axis from an icon
        import sys
        sys.path.insert(0, str(ICON_DIR / "src"))

        embeddings_dir = ICON_DIR / "embeddings"
        subspace_dir = embeddings_dir / "subspace"

        if not (subspace_dir / "basis_vectors.npy").exists():
            print("Error: Subspace not found. Run 'analyze-subspace' command first.")
            sys.exit(1)

        try:
            from iconics_retrieval import IconicsRetriever

            retriever = IconicsRetriever(
                embeddings_path=str(embeddings_dir),
                subspace_path=str(subspace_dir)
            )

            if args.icon_id not in retriever:
                print(f"Error: Icon '{args.icon_id}' not found")
                sys.exit(1)

            icons = retriever.traverse_axis(
                args.icon_id,
                axis=args.axis,
                steps=args.steps,
                direction=args.direction
            )

            if args.output == "json":
                import json as json_mod
                output = {
                    "start_icon": args.icon_id,
                    "axis": args.axis,
                    "direction": args.direction,
                    "steps": args.steps,
                    "path": icons
                }
                print(json_mod.dumps(output, indent=2))
            else:
                print(f"\nTraverse PC{args.axis} from '{args.icon_id}'")
                print(f"Direction: {args.direction}, Steps: {args.steps}")
                print()
                for i, icon in enumerate(icons):
                    marker = " *" if icon == args.icon_id else ""
                    print(f"  {i+1}. {icon}{marker}")

        except ImportError as e:
            print(f"Error: Missing dependency - {e}")
            print("Install required packages: pip install faiss-cpu open_clip_torch torch")
            sys.exit(1)
        except KeyError as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.command == "interpolate":
        # Find icons between two icons
        import sys
        sys.path.insert(0, str(ICON_DIR / "src"))

        embeddings_dir = ICON_DIR / "embeddings"
        subspace_dir = embeddings_dir / "subspace"

        if not (subspace_dir / "basis_vectors.npy").exists():
            print("Error: Subspace not found. Run 'analyze-subspace' command first.")
            sys.exit(1)

        try:
            from iconics_retrieval import IconicsRetriever

            retriever = IconicsRetriever(
                embeddings_path=str(embeddings_dir),
                subspace_path=str(subspace_dir)
            )

            if args.icon_a not in retriever:
                print(f"Error: Icon '{args.icon_a}' not found")
                sys.exit(1)
            if args.icon_b not in retriever:
                print(f"Error: Icon '{args.icon_b}' not found")
                sys.exit(1)

            icons = retriever.interpolate(args.icon_a, args.icon_b, steps=args.steps)

            if args.output == "json":
                import json as json_mod
                output = {
                    "start": args.icon_a,
                    "end": args.icon_b,
                    "steps": args.steps,
                    "path": icons
                }
                print(json_mod.dumps(output, indent=2))
            else:
                print(f"\nInterpolation: '{args.icon_a}' -> '{args.icon_b}'")
                print(f"Steps: {args.steps}")
                print()
                for i, icon in enumerate(icons):
                    t = i / (args.steps - 1) if args.steps > 1 else 0
                    print(f"  {i+1}. {icon} (t={t:.2f})")

        except ImportError as e:
            print(f"Error: Missing dependency - {e}")
            print("Install required packages: pip install faiss-cpu open_clip_torch torch")
            sys.exit(1)
        except KeyError as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.command == "eval-retrieval":
        # Evaluate retrieval quality
        import sys
        sys.path.insert(0, str(ICON_DIR / "src"))

        embeddings_dir = ICON_DIR / "embeddings"
        subspace_dir = embeddings_dir / "subspace"

        ground_truth_path = Path(args.ground_truth)
        if not ground_truth_path.exists():
            print(f"Error: Ground truth file not found: {args.ground_truth}")
            sys.exit(1)

        if not (subspace_dir / "basis_vectors.npy").exists():
            print("Error: Subspace not found. Run 'analyze-subspace' command first.")
            sys.exit(1)

        try:
            from iconics_retrieval import IconicsRetriever
            from iconics_eval import load_ground_truth, evaluate_query_set, compare_methods, format_comparison_table, create_retrieve_fn_from_retriever

            retriever = IconicsRetriever(
                embeddings_path=str(embeddings_dir),
                subspace_path=str(subspace_dir)
            )

            ground_truth = load_ground_truth(ground_truth_path)

            # Compare all three modes
            methods = {
                "raw": create_retrieve_fn_from_retriever(retriever, "raw"),
                "projected": create_retrieve_fn_from_retriever(retriever, "projected"),
                "weighted": create_retrieve_fn_from_retriever(retriever, "weighted"),
            }

            comparison = compare_methods(ground_truth, methods, k=args.k)

            if args.output == "json":
                import json as json_mod
                output = {
                    "ground_truth_path": str(ground_truth_path),
                    "n_queries": len(ground_truth),
                    "k": args.k,
                    "results": comparison
                }
                print(json_mod.dumps(output, indent=2))
            else:
                print(f"\nEvaluation Results (k={args.k}, {len(ground_truth)} queries)")
                print("=" * 60)
                print(format_comparison_table(comparison))

        except ImportError as e:
            print(f"Error: Missing dependency - {e}")
            print("Install required packages: pip install faiss-cpu open_clip_torch torch")
            sys.exit(1)

    elif args.command == "residual":
        # Compute orthogonal residual score
        import sys
        sys.path.insert(0, str(ICON_DIR / "src"))

        embeddings_dir = ICON_DIR / "embeddings"
        subspace_dir = embeddings_dir / "subspace"

        if not (subspace_dir / "basis_vectors.npy").exists():
            print("Error: Subspace not found. Run 'analyze-subspace' command first.")
            sys.exit(1)

        try:
            from iconics_retrieval import IconicsRetriever

            retriever = IconicsRetriever(
                embeddings_path=str(embeddings_dir),
                subspace_path=str(subspace_dir)
            )

            residual_score = retriever.orthogonal_residual_score(args.text)

            # Interpret the score
            if residual_score < 0.3:
                coverage = "high"
                interpretation = "Query is well-represented by the icon library"
            elif residual_score < 0.6:
                coverage = "moderate"
                interpretation = "Query is partially representable by icons"
            else:
                coverage = "low"
                interpretation = "Query concept is outside the icon space"

            if args.output == "json":
                import json as json_mod
                output = {
                    "query": args.text,
                    "residual_score": residual_score,
                    "coverage": coverage,
                    "interpretation": interpretation
                }
                print(json_mod.dumps(output, indent=2))
            else:
                print(f"\nQuery: {args.text}")
                print(f"Residual Score: {residual_score:.4f}")
                print(f"Coverage: {coverage}")
                print(f"Interpretation: {interpretation}")

        except ImportError as e:
            print(f"Error: Missing dependency - {e}")
            print("Install required packages: pip install faiss-cpu open_clip_torch torch")
            sys.exit(1)

    # =========================================================================
    # LLM Integration Command Handlers (Phase 7)
    # =========================================================================

    elif args.command == "batch-query":
        # Batch semantic search for multiple queries
        import sys
        sys.path.insert(0, str(ICON_DIR / "src"))

        embeddings_dir = ICON_DIR / "embeddings"
        subspace_dir = embeddings_dir / "subspace"

        if not (embeddings_dir / "icon_embeddings.npy").exists():
            print("Error: Embeddings not found. Run 'embed' command first.")
            sys.exit(1)

        if not (subspace_dir / "basis_vectors.npy").exists():
            print("Error: Subspace not found. Run 'analyze-subspace' command first.")
            sys.exit(1)

        try:
            from iconics_retrieval import IconicsRetriever

            retriever = IconicsRetriever(
                embeddings_path=str(embeddings_dir),
                subspace_path=str(subspace_dir)
            )

            queries = [q.strip() for q in args.queries.split(",")]
            all_results = {}

            for query in queries:
                results = retriever.retrieve(query, k=args.k, mode=args.mode)
                all_results[query] = [
                    {"icon_id": r.icon_id, "score": r.score, "residual_score": r.residual_score}
                    for r in results
                ]

            if args.output == "json":
                import json as json_mod
                output = {
                    "mode": args.mode,
                    "k": args.k,
                    "queries": all_results
                }
                print(json_mod.dumps(output, indent=2))
            else:
                print(f"\nBatch Query Results (mode: {args.mode}, k: {args.k})")
                print("=" * 60)
                for query, results in all_results.items():
                    print(f"\nQuery: '{query}'")
                    for r in results:
                        print(f"  - {r['icon_id']} (score: {r['score']:.4f})")

        except ImportError as e:
            print(f"Error: Missing dependency - {e}")
            sys.exit(1)

    elif args.command == "provision":
        # Provision icons to a project directory
        import sys
        sys.path.insert(0, str(ICON_DIR / "src"))

        from iconics_provision import IconicsProvisioner, load_catalog

        catalog = load_catalog(str(CATALOG_FILE))
        provisioner = IconicsProvisioner(str(RAW_DIR), catalog)

        # Determine provisioning mode
        if args.manifest:
            # Provision from manifest
            result = provisioner.provision_from_manifest(args.manifest, args.dest)
        elif args.query:
            # Provision from semantic query
            embeddings_dir = ICON_DIR / "embeddings"
            subspace_dir = embeddings_dir / "subspace"

            retriever = None
            if (embeddings_dir / "icon_embeddings.npy").exists() and (subspace_dir / "basis_vectors.npy").exists():
                try:
                    from iconics_retrieval import IconicsRetriever
                    retriever = IconicsRetriever(
                        embeddings_path=str(embeddings_dir),
                        subspace_path=str(subspace_dir)
                    )
                except ImportError:
                    pass

            queries = [q.strip() for q in args.query.split(",")]
            result = provisioner.provision_from_query(
                queries=queries,
                dest=args.dest,
                k=args.k,
                retriever=retriever
            )
        elif args.icons:
            # Provision specific icons
            icon_ids = [i.strip() for i in args.icons.split(",")]
            result = provisioner.provision(
                icon_ids,
                args.dest,
                icon_subdir=args.subdir
            )
        else:
            print("Error: Must specify --icons, --query, or --manifest")
            sys.exit(1)

        if args.output == "json":
            import json as json_mod
            print(json_mod.dumps(result, indent=2))
        else:
            print(f"\nProvisioning Results")
            print("=" * 40)
            print(f"Copied: {len(result['copied'])} icons")
            for icon in result['copied']:
                print(f"  + {icon}")
            if result['skipped']:
                print(f"Skipped: {len(result['skipped'])} (already exist)")
            if result['missing']:
                print(f"Missing: {len(result['missing'])}")
                for icon in result['missing']:
                    print(f"  ! {icon}")
            if result.get('manifest_path'):
                print(f"\nManifest: {result['manifest_path']}")

    elif args.command == "scan-emoji":
        # Scan files for emoji usage
        import sys
        sys.path.insert(0, str(ICON_DIR / "src"))

        from iconics_emoji import EmojiScanner

        # Initialize scanner with optional retriever
        embeddings_dir = ICON_DIR / "embeddings"
        subspace_dir = embeddings_dir / "subspace"

        retriever = None
        if (embeddings_dir / "icon_embeddings.npy").exists() and (subspace_dir / "basis_vectors.npy").exists():
            try:
                from iconics_retrieval import IconicsRetriever
                retriever = IconicsRetriever(
                    embeddings_path=str(embeddings_dir),
                    subspace_path=str(subspace_dir)
                )
            except ImportError:
                pass

        scanner = EmojiScanner(retriever=retriever)

        extensions = [e.strip() for e in args.extensions.split(",")]
        report = scanner.scan(args.path, extensions=extensions, recursive=args.recursive)

        if args.output:
            # Save to file
            import json as json_mod
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to: {args.output}")
        else:
            # Print summary
            print(f"\nEmoji Scan Results")
            print("=" * 40)
            print(f"Files scanned: {report['files_scanned']}")
            print(f"Emojis found: {report['emojis_found']}")
            print(f"Unique emojis: {report['unique_emojis']}")

            if report['emoji_counts']:
                print(f"\nEmoji breakdown:")
                for emoji, count in sorted(report['emoji_counts'].items(), key=lambda x: -x[1])[:10]:
                    print(f"  {emoji}: {count} occurrences")

            if report['occurrences']:
                print(f"\nSample occurrences:")
                for occ in report['occurrences'][:5]:
                    print(f"  {occ['emoji']} in {occ['file']}:{occ['line']}")
                    print(f"    Context: {occ['context'][:50]}...")
                    if occ['suggested_icons']:
                        print(f"    Suggested: {', '.join(occ['suggested_icons'][:3])}")

    elif args.command == "convert-emoji":
        # Convert emojis to icons in files
        import sys
        sys.path.insert(0, str(ICON_DIR / "src"))

        from iconics_emoji import EmojiScanner

        # Load report
        report_path = Path(args.report)
        if not report_path.exists():
            print(f"Error: Report file not found: {args.report}")
            sys.exit(1)

        with open(report_path) as f:
            report = json.load(f)

        scanner = EmojiScanner()

        # Determine if dry run
        dry_run = not args.apply

        result = scanner.convert(report, args.icon_path, dry_run=dry_run)

        if args.output == "json":
            import json as json_mod
            print(json_mod.dumps(result, indent=2))
        else:
            mode = "DRY RUN" if dry_run else "APPLIED"
            print(f"\nEmoji Conversion Results ({mode})")
            print("=" * 40)
            print(f"Files modified: {result['files_modified']}")
            print(f"Replacements: {result['replacements_made']}")

            if result['changes']:
                print(f"\nChanges:")
                for change in result['changes'][:10]:
                    print(f"  {change['file']}:{change['line']}")
                    print(f"    - {change['emoji']} -> {change['icon']}")

            if dry_run and result['replacements_made'] > 0:
                print(f"\nTo apply changes: python3 icon-manager.py convert-emoji --report {args.report} --apply")

    elif args.command == "generate-imports":
        # Generate framework-specific import file
        import sys
        sys.path.insert(0, str(ICON_DIR / "src"))

        from iconics_provision import IconicsProvisioner, load_catalog

        catalog = load_catalog(str(CATALOG_FILE))
        provisioner = IconicsProvisioner(str(RAW_DIR), catalog)

        content = provisioner.generate_imports(
            args.manifest,
            args.format,
            args.output
        )

        print(f"Generated {args.format} imports: {args.output}")
        print(f"  Icons: {content.count('icon')}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
