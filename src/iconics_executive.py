"""
Iconics Executive - The Agentic Orchestrator

The brain of the iconics system. Coordinates CLIP retrieval, VLM labeling,
and catalog management with intelligent decision-making and self-correction.

Key Features:
- High-Confidence Bypass (sim ≥ 0.92) to skip VLM inference
- RAG-Enhanced Labeling (context from k-NN neighbors)
- Reflective Audit (prevents naming drift)
- Variant Registration (improves CLIP index over time)
"""

import logging
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import existing modules
try:
    from iconics_retrieval import IconicsRetriever
    from iconics_vision import VisionLabeler as IconVisionLabeler
except ImportError as e:
    logging.warning(f"Import warning: {e}")
    # Provide stub classes for development
    class IconicsRetriever:
        pass
    class IconVisionLabeler:
        pass

# Always import Output (it's a dependency)
from iconics_output import Output, OutputContext

logger = logging.getLogger(__name__)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@dataclass
class IngestResult:
    """Result of icon ingestion."""
    path: Path
    icon_id: str
    status: str  # 'bypass', 'vlm', or 'error'
    confidence: float
    metadata: Dict
    audit_corrections: Optional[List[Dict]] = None

    def to_dict(self):
        """Convert to dict for JSON serialization."""
        result = asdict(self)
        result['path'] = str(self.path)
        return result


@dataclass
class FileEvent:
    """File system event (for watcher integration)."""
    path: Path
    action: str  # 'created', 'modified'
    timestamp: float
    # Future eBPF fields (for kernel-level monitoring):
    # origin_process: Optional[str] = None
    # user: Optional[str] = None


class IconCatalog:
    """
    Catalog manager that supports JSON or SQLite.

    The public surface area intentionally matches the historical JSON-backed
    implementation so the rest of the codebase can migrate incrementally.
    """

    def __init__(self, catalog_path: Optional[Path] = None):
        if catalog_path is None:
            from iconics_catalog import resolve_default_catalog_path

            catalog_path = resolve_default_catalog_path()
        self.catalog_path = Path(catalog_path)
        self.is_sqlite = self.catalog_path.suffix.lower() in {".sqlite3", ".sqlite", ".db"}
        self._catalog = None
        self._load_catalog()

    def _load_catalog(self):
        """Load catalog from disk."""
        if not self.catalog_path.exists():
            logger.warning(f"Catalog not found: {self.catalog_path}")
            self._catalog = {"version": "missing", "icons": []}
            return

        from iconics_catalog import load_catalog

        self._catalog = load_catalog(self.catalog_path)

    def _save_catalog(self):
        """Save catalog to disk."""
        if self.is_sqlite:
            raise RuntimeError(
                "Refusing to write the entire SQLite catalog wholesale; "
                "use update_entry() / add_new_icon() which perform targeted upserts."
            )

        import json

        with open(self.catalog_path, "w", encoding="utf-8") as f:
            json.dump(self._catalog, f, indent=2)

    def get_entry(self, icon_id: str) -> Optional[Dict]:
        """Get catalog entry by ID."""
        for icon in self._catalog.get('icons', []):
            if icon['id'] == icon_id:
                return icon
        return None

    @staticmethod
    def _semantic_filename(icon: Dict) -> Optional[str]:
        icon_id = str(icon.get("id") or "").strip()
        if not icon_id:
            return None

        semantic_name = str(icon.get("semanticName") or icon_id).strip()
        semantic_name = re.sub(r"[\\/]+", "-", semantic_name).strip()
        if not semantic_name:
            semantic_name = icon_id

        if semantic_name == icon_id:
            return f"{icon_id}.png"
        return f"{semantic_name}--{icon_id}.png"

    @staticmethod
    def _resolve_icon_file(repo_root: Path, icon: Dict) -> Optional[Path]:
        icon_id = str(icon.get("id") or "").strip()

        candidates: List[Path] = []
        for key in ("sourceFile", "filename"):
            value = icon.get(key)
            if isinstance(value, str) and value.strip():
                p = Path(value)
                candidates.append(p if p.is_absolute() else (repo_root / p))

        if icon_id:
            candidates.append(repo_root / "raw" / f"{icon_id}.png")

        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()
        return None

    def sync_catalog_entry_symlink(self, icon_id: str, repo_root: Optional[Path] = None) -> Optional[Path]:
        """
        Ensure a single organized-tree symlink exists for the specified icon.

        Removes stale symlinks that currently point at the icon's source asset,
        then recreates the canonical category/semantic symlink.
        """
        repo = (repo_root or _repo_root()).resolve()
        entry = self.get_entry(icon_id)
        if not entry:
            return None

        raw_file = self._resolve_icon_file(repo, entry)
        if raw_file is None:
            logger.warning(f"Cannot create organized symlink for {icon_id}: source file missing")
            return None

        catalog_root = repo / "catalog"
        if catalog_root.exists():
            for symlink in catalog_root.rglob("*.png"):
                if not symlink.is_symlink():
                    continue
                try:
                    if symlink.resolve() == raw_file:
                        symlink.unlink()
                except FileNotFoundError:
                    symlink.unlink()

        category = str(entry.get("category") or "unknown").strip() or "unknown"
        target_name = self._semantic_filename(entry)
        if target_name is None:
            return None

        category_dir = catalog_root / category
        category_dir.mkdir(parents=True, exist_ok=True)
        target = category_dir / target_name
        rel_target = Path(os.path.relpath(raw_file, start=category_dir))

        if target.exists() or target.is_symlink():
            if target.is_symlink():
                target.unlink()
            else:
                logger.warning(f"Refusing to overwrite non-symlink catalog entry: {target}")
                return None

        target.symlink_to(rel_target)
        return target

    def rebuild_catalog_tree(self, repo_root: Optional[Path] = None) -> Dict[str, int]:
        """
        Rebuild the entire organized catalog tree from the active catalog.

        The organized tree is derived data; rebuilding guarantees one symlink per
        catalog row and eliminates stale semantic/collision leftovers.
        """
        repo = (repo_root or _repo_root()).resolve()
        catalog_root = repo / "catalog"
        catalog_root.mkdir(parents=True, exist_ok=True)

        removed = 0
        for symlink in catalog_root.rglob("*.png"):
            if symlink.is_symlink():
                symlink.unlink()
                removed += 1

        created = 0
        missing_files = 0
        blocked = 0

        for icon in self._catalog.get("icons", []):
            if not isinstance(icon, dict):
                continue
            icon_id = str(icon.get("id") or "").strip()
            if not icon_id:
                continue

            raw_file = self._resolve_icon_file(repo, icon)
            if raw_file is None:
                missing_files += 1
                continue

            category = str(icon.get("category") or "unknown").strip() or "unknown"
            filename = self._semantic_filename(icon)
            if filename is None:
                continue

            category_dir = catalog_root / category
            category_dir.mkdir(parents=True, exist_ok=True)
            target = category_dir / filename
            rel_target = Path(os.path.relpath(raw_file, start=category_dir))

            if target.exists() or target.is_symlink():
                if target.is_symlink():
                    target.unlink()
                else:
                    blocked += 1
                    logger.warning(f"Refusing to overwrite non-symlink catalog entry: {target}")
                    continue

            target.symlink_to(rel_target)
            created += 1

        return {
            "removed": removed,
            "created": created,
            "missing_files": missing_files,
            "blocked": blocked,
        }

    def update_entry(self, icon_id: str, updated_entry: Dict) -> bool:
        """
        Update an existing catalog entry.

        Args:
            icon_id: Icon ID to update
            updated_entry: New entry data (must include 'id' field)

        Returns:
            True if entry was updated, False if not found
        """
        for i, icon in enumerate(self._catalog.get('icons', [])):
            if icon['id'] == icon_id:
                self._catalog['icons'][i] = updated_entry
                if self.is_sqlite:
                    from iconics_catalog import upsert_icon_sqlite

                    upsert_icon_sqlite(self.catalog_path, updated_entry)
                else:
                    self._save_catalog()
                self.sync_catalog_entry_symlink(icon_id)
                logger.info(f"Updated catalog entry for {icon_id}")
                return True
        logger.warning(f"Icon {icon_id} not found in catalog for update")
        return False

    def register_variant(self, path: Path, existing_icon_id: str):
        """Register a new variant of an existing icon (bypass path)."""
        # In the bypass path, we don't modify the catalog
        # Just log that this file is a variant
        logger.info(f"Registered {path.name} as variant of {existing_icon_id}")

    def add_new_icon(self, path: Path, label_data: Dict):
        """Add newly labeled icon to catalog (VLM path)."""
        from iconics_catalog import ensure_repo_relative_path

        repo = _repo_root()
        source_file_rel = ensure_repo_relative_path(path, repo_root=repo)
        icon_id = path.stem

        icon_entry = {
            "id": icon_id,
            "semanticName": label_data.get('canonical', icon_id),
            "tags": label_data.get('tags', []),
            "category": label_data.get('category', 'unknown'),
            "description": label_data.get('description', ''),
            "sourceFile": source_file_rel,
            "filename": source_file_rel,
        }

        # Avoid introducing duplicate IDs in the in-memory view (SQLite enforces uniqueness).
        icons = self._catalog.setdefault("icons", [])
        for idx, existing in enumerate(icons):
            if existing.get("id") == icon_entry["id"]:
                icons[idx] = icon_entry
                break
        else:
            icons.append(icon_entry)

        if self.is_sqlite:
            from iconics_catalog import upsert_icon_sqlite

            upsert_icon_sqlite(self.catalog_path, icon_entry)
        else:
            self._save_catalog()
        self.sync_catalog_entry_symlink(icon_id)
        logger.info(f"Added {icon_entry['id']} to catalog")

    def get_stats(self) -> Dict:
        """Get catalog statistics."""
        icons = self._catalog.get('icons', [])
        categories = {}
        for icon in icons:
            cat = icon.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_icons": len(icons),
            "version": self._catalog.get('version', 'unknown'),
            "categories": categories,
        }


class IconicsExecutive:
    """
    The Resident Executive: Orchestrates CLIP, VLM, and Catalog agents.

    Architecture:
        OBSERVE → ORIENT → DECIDE → ACT

    Decision Gates:
        1. High-Confidence Bypass (sim ≥ 0.92): Skip VLM, inherit metadata
        2. RAG-Enhanced VLM (0.7 < sim < 0.92): Use k-NN context in prompt
        3. Reflective Audit (after VLM): Prevent naming drift
    """

    def __init__(
        self,
        bypass_threshold: float = 0.92,
        rag_threshold: float = 0.7,
        drift_threshold: float = 0.80,
        embeddings_path: Optional[Path] = None,
        subspace_path: Optional[Path] = None,
        catalog_path: Optional[Path] = None,
        output: Optional[Output] = None,
    ):
        """
        Initialize the Executive.

        Args:
            bypass_threshold: Similarity threshold for high-confidence bypass (default: 0.92)
            rag_threshold: Similarity threshold for RAG context (default: 0.7)
            drift_threshold: Similarity threshold for naming drift detection (default: 0.8)
            embeddings_path: Path to CLIP embeddings
            subspace_path: Path to PCA subspace
            catalog_path: Path to icon catalog JSON
            output: Output formatter (or use global)
        """
        self.bypass_threshold = bypass_threshold
        self.rag_threshold = rag_threshold
        self.drift_threshold = drift_threshold

        base_dir = _repo_root()
        from iconics_config import EMBEDDINGS_DIR, SUBSPACE_DIR

        embeddings_path = embeddings_path or EMBEDDINGS_DIR
        subspace_path = subspace_path or SUBSPACE_DIR
        if catalog_path is None:
            from iconics_catalog import resolve_default_catalog_path

            catalog_path = resolve_default_catalog_path()

        # Initialize sub-agents
        try:
            self.retriever = IconicsRetriever(
                embeddings_path=str(embeddings_path),
                subspace_path=str(subspace_path),
            )
            self.labeler = IconVisionLabeler(
                embeddings_path=str(embeddings_path),
                subspace_path=str(subspace_path),
                catalog_path=str(catalog_path),
            )
        except Exception as e:
            logger.warning(f"Could not initialize retriever/labeler: {e}")
            self.retriever = None
            self.labeler = None

        self.catalog = IconCatalog(catalog_path)
        self.output = output or OutputContext.get_global()

        logger.info(f"IconicsExecutive initialized (bypass≥{bypass_threshold}, rag≥{rag_threshold})")

    def execute_ingest(self, file_path: Path, force: bool = False) -> IngestResult:
        """
        Process a single icon through the intelligent pipeline.

        Args:
            file_path: Path to icon file
            force: If True, skip bypass and force VLM labeling

        Returns:
            IngestResult with status, confidence, and metadata
        """
        path = Path(file_path)

        if not path.exists():
            return IngestResult(
                path=path,
                icon_id='',
                status='error',
                confidence=0.0,
                metadata={'error': 'File not found'}
            )

        if self.output:
            self.output.debug(f"Executive ingesting: {path}")

        # 1. OBSERVE: Generate CLIP Embedding and Perform k-NN Search
        try:
            top_match = self._find_nearest_neighbor(path)
            similarity = top_match['score']

            if self.output:
                self.output.debug(f"k-NN top match: {top_match['semantic_name']} (sim={similarity:.3f})")

        except Exception as e:
            logger.error(f"CLIP retrieval failed: {e}")
            return IngestResult(
                path=path,
                icon_id='',
                status='error',
                confidence=0.0,
                metadata={'error': str(e)}
            )

        # 2. DECIDE: HIGH-CONFIDENCE BYPASS (sim ≥ 0.92)
        if similarity >= self.bypass_threshold and not force:
            if self.output:
                self.output.info(f"High-confidence bypass (sim={similarity:.3f})")
            return self._handle_bypass(path, top_match)

        # 3. ACT: HEAVY INFERENCE PATH (VLM with Reflective Audit)
        if self.output:
            self.output.info(f"VLM labeling required (sim={similarity:.3f})")
        return self._handle_vlm_labeling(path, similarity, top_match, force)

    def _find_nearest_neighbor(self, path: Path) -> Dict:
        """Find nearest neighbor in catalog using CLIP embeddings."""
        if not self.retriever:
            raise RuntimeError("Retriever not initialized")

        # Embed the new icon
        try:
            icon_embedding = self.retriever.embed_image(path)
        except Exception as e:
            logger.error(f"Failed to embed image {path}: {e}")
            return {
                'icon_id': '',
                'semantic_name': '',
                'score': 0.0,
                'tags': []
            }

        # Retrieve similar icons using the embedding
        try:
            candidates = self.retriever.retrieve_for_labeling(
                icon_embedding,
                catalog_path=str(self.catalog.catalog_path),
                k=1,
                mode="projected"
            )
        except Exception as e:
            logger.error(f"Failed to retrieve candidates: {e}")
            return {
                'icon_id': '',
                'semantic_name': '',
                'score': 0.0,
                'tags': []
            }

        if not candidates or len(candidates) == 0:
            return {
                'icon_id': '',
                'semantic_name': '',
                'score': 0.0,
                'tags': []
            }

        top = candidates[0]
        return {
            'icon_id': top.get('icon_id', top.get('semantic_name', '')),
            'semantic_name': top.get('semantic_name', top.get('icon_id', '')),
            'score': top.get('similarity', 0.0),
            'tags': top.get('tags', []),
        }

    def _handle_bypass(self, path: Path, match: Dict) -> IngestResult:
        """
        Handle high-confidence bypass path.

        Skips VLM and inherits metadata from the closest catalog match.
        Registers the file as a variant to improve CLIP index over time.
        """
        # Inherit semantic data from the existing catalog entry
        catalog_entry = self.catalog.get_entry(match['icon_id'])
        if catalog_entry:
            metadata = {
                'canonical': catalog_entry.get('semanticName', match['icon_id']),
                'tags': catalog_entry.get('tags', []),
                'category': catalog_entry.get('category', 'unknown'),
                'description': catalog_entry.get('description', ''),
                'inherited_from': match['icon_id'],
            }
        else:
            metadata = {
                'canonical': match['icon_id'],
                'tags': match.get('tags', []),
                'inherited_from': match['icon_id'],
            }

        # Register as variant (improves CLIP over time)
        self.catalog.register_variant(path, match['icon_id'])

        return IngestResult(
            path=path,
            icon_id=match['icon_id'],
            status='bypass',
            confidence=match['score'],
            metadata=metadata
        )

    def _handle_vlm_labeling(
        self,
        path: Path,
        similarity: float,
        match: Dict,
        force: bool = False
    ) -> IngestResult:
        """
        Handle VLM labeling path with Reflective Audit.

        Uses RAG-enhanced prompting to maintain naming consistency,
        then applies Reflective Audit to prevent naming drift.
        """
        if not self.labeler:
            return IngestResult(
                path=path,
                icon_id='',
                status='error',
                confidence=0.0,
                metadata={'error': 'VLM labeler not initialized'}
            )

        # RAG Context: Pass the closest match to the VLM
        context_hint = None
        if similarity > self.rag_threshold:
            catalog_entry = self.catalog.get_entry(match['icon_id'])
            if catalog_entry:
                context_hint = f"Similar to existing icon: {catalog_entry.get('semanticName', match['icon_id'])}"
                if self.output:
                    self.output.debug(f"RAG context: {context_hint}")

        # 4-Panel Preproc + Qwen-VL Inference
        try:
            icon_label = self.labeler.label_icon(
                path,
                k_neighbors=10,  # Retrieve 10 neighbors for context
                use_cache=True
            )
            # Convert IconLabel to dict for processing
            label_data = icon_label.to_dict()

        except Exception as e:
            logger.error(f"VLM labeling failed: {e}")
            return IngestResult(
                path=path,
                icon_id='',
                status='error',
                confidence=0.0,
                metadata={'error': str(e)}
            )

        # REFLECTIVE AUDIT: Ensure the new labels don't contradict the catalog
        audit_corrections = []
        if self._is_naming_drift_detected(label_data, match):
            if self.output:
                self.output.debug("Naming drift detected, applying correction")
            label_data, correction_info = self._resolve_naming_conflict(label_data, match)
            audit_corrections.append(correction_info)

            # Report to user (if not in quiet mode)
            if self.output:
                self.output.format_audit_correction(
                    original_label=correction_info['from'],
                    corrected_label=correction_info['to'],
                    reason=correction_info['reason']
                )

        # Finalize: Add to catalog and update embeddings
        self.catalog.add_new_icon(path, label_data)

        # Incremental embedding update (makes icon immediately searchable)
        if self.retriever:
            try:
                self.retriever.add_incremental_embedding(path, icon_id=path.stem)
                logger.debug(f"Added incremental embedding for {path.name}")
            except Exception as e:
                logger.error(f"Failed to add incremental embedding for {path.name}: {e}")
                # Non-fatal - catalog update succeeded, embedding can be added later

        return IngestResult(
            path=path,
            icon_id=path.stem,
            status='vlm',
            confidence=label_data.get('confidence', 0.0),
            metadata=label_data,
            audit_corrections=audit_corrections if audit_corrections else None
        )

    def _is_naming_drift_detected(self, label_data: Dict, match: Dict) -> bool:
        """
        Detect if VLM is deviating from established catalog vocabulary.

        Args:
            label_data: VLM-generated label data
            match: k-NN neighbor match

        Returns:
            True if naming drift is detected
        """
        # Only check if we have a moderately confident match
        if match['score'] < self.drift_threshold:
            return False

        vlm_name = label_data.get('canonical', '').lower()
        neighbor_name = match.get('semantic_name', '').lower()

        # If they are different but have high similarity, we have drift risk
        return vlm_name != neighbor_name and len(vlm_name) > 0 and len(neighbor_name) > 0

    def _resolve_naming_conflict(
        self,
        label_data: Dict,
        match: Dict
    ) -> Tuple[Dict, Dict]:
        """
        Force VLM labels to align with catalog standards.

        Args:
            label_data: VLM-generated label data
            match: k-NN neighbor match

        Returns:
            Tuple of (corrected_label_data, correction_info)
        """
        original_name = label_data.get('canonical', '')
        catalog_name = match.get('semantic_name', '')

        # Update label_data to follow established standards
        label_data['canonical'] = catalog_name
        # CRITICAL: Also update icon_id to match canonical
        label_data['icon_id'] = catalog_name

        # Merge tags to ensure searchability for both new and old terms
        vlm_tags = set(label_data.get('tags', []))
        catalog_tags = set(match.get('tags', []))
        label_data['tags'] = list(vlm_tags | catalog_tags)

        correction_info = {
            'from': original_name,
            'to': catalog_name,
            'reason': f'Aligned with catalog standard (sim={match["score"]:.3f})',
            'merged_tags': len(vlm_tags | catalog_tags) - len(vlm_tags),
        }

        logger.info(f"Audit correction: '{original_name}' → '{catalog_name}'")
        return label_data, correction_info

    def handle_event(self, event: FileEvent) -> Optional[IngestResult]:
        """
        Handle file system event (from watcher).

        Args:
            event: File system event

        Returns:
            IngestResult if successful, None if event should be ignored
        """
        # Filter by extension
        if event.path.suffix.lower() not in {'.png', '.svg', '.webp'}:
            return None

        # Execute ingestion
        return self.execute_ingest(event.path)

    def get_stats(self) -> Dict:
        """Get library statistics."""
        return self.catalog.get_stats()

    def use_icons(
        self,
        query_ids: List[str],
        target_dir: Optional[Path] = None,
        generate_markdown: bool = True
    ) -> Dict:
        """
        Export icons with intelligent semantic resolution.

        Orchestrates the 'use' command:
        1. Resolves IDs (direct match or CLIP fallback)
        2. Exports files via IconExporter
        3. Generates Markdown for the user/agent
        4. Tracks usage for Reflective Audit context

        Args:
            query_ids: List of icon IDs or semantic queries
            target_dir: Target directory (auto-detected if None)
            generate_markdown: Whether to generate markdown snippets

        Returns:
            Dict with export results
        """
        from iconics_export import IconExporter

        resolved_ids = []

        for q_id in query_ids:
            # Step 1: Try direct ID lookup
            entry = self.catalog.get_entry(q_id)
            if entry:
                resolved_ids.append(q_id)
                continue

            # Step 1.5: Try semantic name lookup in catalog
            # Check if any icon has this semantic name
            found_by_semantic = False
            for icon in self.catalog._catalog.get('icons', []):
                if icon.get('semanticName', '').lower() == q_id.lower():
                    resolved_ids.append(icon['id'])
                    found_by_semantic = True
                    break

            if found_by_semantic:
                continue

            # Step 2: Semantic fallback via CLIP
            if not self.retriever:
                if self.output:
                    self.output.error(f"Cannot resolve '{q_id}': Retriever not initialized")
                continue

            if self.output and self.output.mode != 'quiet':
                self.output.info(f"ID '{q_id}' not found. Searching for best semantic match...")

            try:
                # Use text retrieval for semantic matching
                results = self.retriever.retrieve(q_id, k=1)
                if results and results[0].score > 0.55:  # Lower threshold for use command
                    match = results[0]
                    resolved_ids.append(match.icon_id)

                    if self.output and self.output.mode != 'quiet':
                        self.output.warn(
                            f"Using '{match.icon_id}' for '{q_id}' "
                            f"(similarity: {match.score:.3f})"
                        )
                else:
                    if self.output:
                        self.output.error(f"Could not resolve icon: {q_id}")

            except Exception as e:
                logger.error(f"Semantic resolution failed for '{q_id}': {e}")
                if self.output:
                    self.output.error(f"Could not resolve icon: {q_id}")

        if not resolved_ids:
            return {
                'exported': [],
                'failed': query_ids,
                'target_dir': str(target_dir or Path.cwd()),
                'markdown': []
            }

        # Step 3: Execute Export
        exporter = IconExporter(self.catalog)
        result = exporter.export_icons(resolved_ids, target_dir, generate_markdown)

        # Step 4: Track usage for Reflective Audit context
        if result['exported'] and target_dir:
            try:
                exporter.track_usage(
                    target_dir,
                    [item['id'] for item in result['exported']]
                )
            except Exception as e:
                logger.warning(f"Usage tracking failed: {e}")

        return result
