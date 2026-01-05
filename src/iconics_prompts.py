"""
Iconics VLM Prompts - Reflective Alignment System

Prompts that transform the VLM from a simple captioning tool into a
"Librarian Agent" that respects existing catalog taxonomy.

System 2 Reasoning: Context-aware labeling with drift prevention.
"""

from typing import Dict, List, Optional


# System Prompt: Establishes VLM Persona
LIBRARIAN_SYSTEM_PROMPT = """### Role
You are the "Iconics Cataloger." Your goal is to label new visual assets so they fit perfectly into a pre-existing design system.

### Guidelines
1. **Consistency First:** If a "Context Hint" is provided, use its vocabulary. Do not invent new terms if a similar concept already exists in the catalog.
2. **Semantic Precision:** Use clear, hyphenated lowercase IDs (e.g., 'security-shield-open').
3. **Tagging:** Provide tags that are functional, not just descriptive (e.g., use 'save' instead of just 'floppy-disk').

### Output Format
Return ONLY a JSON object with these keys:
- "canonical": (The primary semantic name)
- "category": (The most relevant library category: ui, files, security, network, tools, development, or emoji)
- "tags": (A list of 5-8 descriptive and functional keywords)
- "description": (A one-sentence technical description)
- "confidence": (Your confidence in this label from 0.0 to 1.0, where 1.0 is completely certain)

Do not include any other text, explanations, or markdown formatting. Only return the JSON object.
"""


def build_ingestion_prompt(
    context_hint: Optional[str] = None,
    neighbor_match: Optional[Dict] = None,
    k_neighbors: Optional[List[Dict]] = None
) -> str:
    """
    Build the dynamic ingestion prompt with RAG context.

    This prompt is constructed by the IconicsExecutive for every new icon drop,
    passing the k-NN match as a constraint to anchor the VLM to existing vocabulary.

    Args:
        context_hint: Optional context string
        neighbor_match: Top k-NN match with semantic_name, tags, score
        k_neighbors: List of k nearest neighbors for additional context

    Returns:
        Formatted prompt string
    """
    prompt_parts = ["Analyze this icon and provide structured metadata."]

    # RAG Context: Anchor to existing vocabulary
    if neighbor_match:
        semantic_name = neighbor_match.get('semantic_name', '')
        tags = neighbor_match.get('tags', [])
        score = neighbor_match.get('score', 0.0)

        prompt_parts.append(f"\n[CONTEXT HINT]")
        prompt_parts.append(
            f"This icon has been identified as visually similar to our existing asset: '{semantic_name}'."
        )

        if tags:
            prompt_parts.append(f"Existing Tags: {', '.join(tags)}")

        prompt_parts.append(f"Similarity Score: {score:.3f}")

        prompt_parts.append("\n[TASK]")

        if score >= 0.85:
            prompt_parts.append(
                f"1. This icon appears to be a variant of '{semantic_name}'. "
                f"Use '{semantic_name}' as the base for the 'canonical' name, "
                f"adding only size or variant suffixes if needed."
            )
        elif score >= 0.70:
            prompt_parts.append(
                f"1. This icon is similar to '{semantic_name}'. "
                f"If it represents the same concept, use '{semantic_name}' as the canonical name. "
                f"If it's different, explain why in the 'description'."
            )
        else:
            prompt_parts.append(
                "1. This appears to be a new icon concept. Provide a unique canonical name."
            )

        prompt_parts.append("2. Ensure the 'tags' include both the new visual elements and the existing functional tags.")
        prompt_parts.append("3. Choose the most appropriate category from: ui, files, security, network, tools, development, emoji.")

    else:
        # No neighbor context
        prompt_parts.append("\n[TASK]")
        prompt_parts.append("1. Provide a unique, descriptive canonical name.")
        prompt_parts.append("2. Include 5-8 functional and descriptive tags.")
        prompt_parts.append("3. Choose the most appropriate category from: ui, files, security, network, tools, development, emoji.")
        prompt_parts.append("4. Write a clear, one-sentence technical description.")

    # Additional k-NN context for broader awareness
    if k_neighbors and len(k_neighbors) > 1:
        prompt_parts.append("\n[RELATED ICONS IN CATALOG]")
        for i, neighbor in enumerate(k_neighbors[:5], 1):  # Top 5
            name = neighbor.get('semantic_name', 'unknown')
            neighbor_tags = neighbor.get('tags', [])
            prompt_parts.append(
                f"  {i}. {name} (tags: {', '.join(neighbor_tags[:3])})"
            )

    # Custom context hint
    if context_hint:
        prompt_parts.append(f"\n[ADDITIONAL CONTEXT]\n{context_hint}")

    return "\n".join(prompt_parts)


def build_correction_prompt(
    original_label: str,
    catalog_standard: str,
    original_tags: List[str],
    catalog_tags: List[str],
    similarity_score: float
) -> str:
    """
    Build the Reflective Correction re-prompt for naming drift resolution.

    This prompt is triggered when the _is_naming_drift_detected method catches
    a conflict (e.g., VLM insists on "Mail" while catalog uses "Envelope").

    Args:
        original_label: VLM-suggested canonical name
        catalog_standard: Catalog's standard name for this concept
        original_tags: VLM-suggested tags
        catalog_tags: Catalog's standard tags
        similarity_score: CLIP similarity to catalog entry

    Returns:
        Re-alignment prompt string
    """
    prompt = f"""### RE-ALIGNMENT REQUEST

You suggested the canonical name '{original_label}'.
However, our library standard for this visual metaphor is '{catalog_standard}'.

Based on a CLIP similarity score of {similarity_score:.3f}, this icon should be cataloged as a variant of '{catalog_standard}'.

Please RE-GENERATE your JSON output with these corrections:

1. Set "canonical" to: "{catalog_standard}"
2. Merge your tags with the existing standard tags:
   - Your tags: {', '.join(original_tags)}
   - Standard tags: {', '.join(catalog_tags)}
   - Use all unique tags from both sets

3. Update the description to reflect that this is a variant of '{catalog_standard}'

Return ONLY the corrected JSON object.
"""
    return prompt


def build_batch_context_prompt(
    icons_in_batch: List[str],
    batch_index: int,
    total_batches: int
) -> str:
    """
    Build a context prompt for batch ingestion.

    When processing multiple icons at once (e.g., from watcher), provide
    context about the batch to help the VLM understand relationships.

    Args:
        icons_in_batch: List of icon filenames being processed together
        batch_index: Current batch number (1-indexed)
        total_batches: Total number of batches

    Returns:
        Batch context string
    """
    prompt = f"""[BATCH CONTEXT]
Processing batch {batch_index} of {total_batches} ({len(icons_in_batch)} icons in this batch).

Icons being processed together:
{chr(10).join(f'  - {name}' for name in icons_in_batch)}

These icons may be related (e.g., different sizes of the same concept, or a themed set).
Consider semantic relationships when generating names and tags.
"""
    return prompt


# Category definitions with examples
CATEGORY_GUIDELINES = {
    'ui': 'User interface controls: buttons, arrows, checkboxes, navigation, menus, close, delete, home',
    'files': 'File and document management: folders, documents, PDFs, photos, videos, archives, save, open',
    'security': 'Security and privacy: locks, shields, keys, certificates, authentication, encryption, hide, show',
    'network': 'Network and connectivity: cloud, globe, wifi, network diagrams, connections, servers',
    'tools': 'Tools and utilities: search, settings, print, export, import, battery, power, toolbox',
    'development': 'Software development: databases, consoles, applications, scripts, plugins, errors, APIs',
    'emoji': 'Expressive icons: emotions, characters, reactions, gestures'
}


def get_category_hint(category: str) -> str:
    """
    Get category guidelines for the VLM.

    Args:
        category: Category name

    Returns:
        Category description with examples
    """
    return CATEGORY_GUIDELINES.get(category, "General purpose icon")


def build_multi_panel_analysis_prompt(panel_count: int = 4) -> str:
    """
    Build prompt for multi-panel preprocessing analysis.

    The iconics system uses 4-panel preprocessing (gray matte, white matte,
    tight crop, edges) to give the VLM multiple perspectives.

    Args:
        panel_count: Number of panels in the composite image

    Returns:
        Analysis instruction prompt
    """
    return f"""[VISUAL ANALYSIS INSTRUCTION]
You are viewing a {panel_count}-panel composite image showing different perspectives of the same icon:
- Panel 1: Gray matte background (neutral context)
- Panel 2: White matte background (high contrast)
- Panel 3: Tight crop (detail focus)
- Panel 4: Edge detection (shape analysis)

Analyze ALL panels to understand:
1. The core visual metaphor (what concept does this icon represent?)
2. Shape and geometry (simple/complex, geometric/organic)
3. Visual style (flat, skeuomorphic, minimal, detailed)
4. Distinctive features (unique elements that define this icon)

Use this multi-perspective analysis to generate accurate metadata.
"""
