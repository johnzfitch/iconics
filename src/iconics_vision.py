"""
Vision-Powered Icon Labeling System
Uses Qwen2.5-VL or InternVL3 with retrieval augmentation for semantic labeling

Features:
- 4-panel composite preprocessing (gray matte, white matte, tight crop, edges)
- Retrieval-augmented prompting with k-NN context
- High-confidence retrieval bypass (skip VLM if similarity >= threshold)
- Native HuggingFace batch inference
- Optional constrained decoding with Outlines (guaranteed valid JSON)
- Flash attention for faster inference
- Result caching
"""

import json
import logging
import hashlib
import os
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Literal, Union
from dataclasses import dataclass

import torch
import numpy as np
from PIL import Image

# Configure HuggingFace for local-first operation
# Models must be pre-downloaded during setup, not at runtime
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HOME", os.path.expanduser("~/.cache/huggingface"))

# Import original preprocessing (4-panel composite)
from iconics_preprocessing import preprocess_icon
from iconics_retrieval import IconicsRetriever
from iconics_taxonomy import ALLOWED_CATEGORIES, coerce_category

logger = logging.getLogger(__name__)

# Retrieval similarity threshold to skip VLM inference
HIGH_CONFIDENCE_THRESHOLD = 0.92

# JSON schema for constrained decoding
ICON_LABEL_SCHEMA = {
    "type": "object",
    "properties": {
        "canonical": {"type": "string", "minLength": 1},
        "tags": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "category": {"enum": ALLOWED_CATEGORIES},
        "description": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "alternates": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["canonical", "tags", "category", "description", "confidence"]
}


@dataclass
class IconLabel:
    """Structured icon label result."""
    canonical: str
    tags: List[str]
    category: str
    description: str
    confidence: float
    alternates: List[str]
    retrieval_candidates: List[Dict]

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'canonical': self.canonical,
            'tags': self.tags,
            'category': self.category,
            'description': self.description,
            'confidence': self.confidence,
            'alternates': self.alternates,
            'retrieval_candidates': self.retrieval_candidates
        }


class VisionLabeler:
    """
    Vision model wrapper for icon semantic labeling.
    
    Supports:
    - Qwen2.5-VL-7B-Instruct (default, fits on 24GB GPU)
    - InternVL3-14B (8-bit/4-bit quantized)
    
    Features:
    - 4-panel composite preprocessing for pixel-art clarity
    - High-confidence retrieval bypass
    - Native batch inference
    - Optional constrained decoding (Outlines)
    - Flash attention
    - Result caching
    """

    def __init__(
        self,
        model_name: Literal["qwen2.5-vl-7b", "internvl3-14b"] = "qwen2.5-vl-7b",
        device: str = "cuda",
        quantization: Optional[Literal["8bit", "4bit"]] = None,
        embeddings_path: str = "embeddings",
        subspace_path: str = "embeddings/subspace",
        catalog_path: str = "icon-catalog.json",
        cache_dir: Optional[Path] = None,
        use_flash_attn: bool = True,
        use_fast_processor: bool = False,
        use_constrained_decoding: bool = False,
        retrieval_bypass_threshold: float = HIGH_CONFIDENCE_THRESHOLD
    ):
        """
        Initialize vision labeler.
        
        Args:
            model_name: Which VLM to use
            device: Base device ("cuda" or "cpu")
            quantization: Optional quantization ("8bit" or "4bit")
            embeddings_path: Path to CLIP embeddings
            subspace_path: Path to subspace data
            catalog_path: Path to icon-catalog.json
            cache_dir: Directory for caching results
            use_flash_attn: Use flash attention if available
            use_constrained_decoding: Use Outlines for guaranteed valid JSON
            retrieval_bypass_threshold: Skip VLM if retrieval similarity >= this
        """
        self.model_name = model_name
        self.device = device
        self.quantization = quantization
        self.catalog_path = Path(catalog_path)
        self.use_flash_attn = use_flash_attn
        self.use_fast_processor = use_fast_processor
        self.use_constrained_decoding = use_constrained_decoding
        self.retrieval_bypass_threshold = retrieval_bypass_threshold

        # Cache directory
        self.cache_dir = Path(cache_dir) if cache_dir else Path("vision_cache")
        self.cache_dir.mkdir(exist_ok=True)

        # Catalog cache (avoid repeated JSON loads)
        self._catalog_cache: Optional[Dict] = None

        # Initialize retrieval system
        logger.info("Initializing retrieval system...")
        try:
            self.retriever = IconicsRetriever(
                embeddings_path=embeddings_path,
                subspace_path=subspace_path
            )
            logger.info(f"Retrieval system loaded: {len(self.retriever)} icons")
        except ModuleNotFoundError as e:
            # Common local-only case: missing CLIP deps (e.g. open_clip).
            # We can still run the VLM without retrieval augmentation.
            logger.warning(f"Retrieval system unavailable (missing dependency): {e}")
            self.retriever = None
        except Exception as e:
            logger.warning(f"Retrieval system unavailable: {e}")
            self.retriever = None

        # Model lazy-loaded on first use
        self.model = None
        self.processor = None
        self._model_loaded = False
        
        # Outlines generator (lazy-loaded if enabled)
        self._outlines_generator = None

    def _get_catalog_lookup(self) -> Dict:
        """Get or load catalog lookup dict (cached)."""
        if self._catalog_cache is None:
            from iconics_catalog import load_catalog

            data = load_catalog(self.catalog_path)
            self._catalog_cache = {icon["id"]: icon for icon in data["icons"]}
        return self._catalog_cache

    def _load_model(self):
        """Lazy-load vision model."""
        if self._model_loaded:
            return

        logger.info(f"Loading vision model: {self.model_name}")

        if self.model_name == "qwen2.5-vl-7b":
            self._load_qwen_model()
        elif self.model_name == "internvl3-14b":
            self._load_internvl_model()
        else:
            raise ValueError(f"Unknown model: {self.model_name}")

        self._model_loaded = True
        logger.info("Model loaded successfully")
        
        # Initialize Outlines if enabled
        if self.use_constrained_decoding:
            self._init_outlines()

    def _load_qwen_model(self):
        """Load Qwen2.5-VL-7B-Instruct model."""
        # CRITICAL: Qwen2_5_VL (with underscore) not Qwen2VL
        from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor

        model_id = "Qwen/Qwen2.5-VL-7B-Instruct"

        # Load processor.
        #
        # Transformers started defaulting to a "fast" processor for Qwen2VL, which can
        # change outputs slightly. For consistent, high-quality cataloging runs, we
        # default to the checkpoint-compatible "slow" processor unless explicitly enabled.
        self.processor = AutoProcessor.from_pretrained(model_id, use_fast=self.use_fast_processor)

        # Quantization config
        quantization_config = None
        if self.quantization == "8bit":
            from transformers import BitsAndBytesConfig
            quantization_config = BitsAndBytesConfig(load_in_8bit=True)
        elif self.quantization == "4bit":
            from transformers import BitsAndBytesConfig
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16
            )

        # Attention implementation
        #
        # FlashAttention is an optional performance optimization. Many environments
        # (especially isolated uv venvs) won't have it installed; avoid a scary warning
        # in that common case and just use SDPA.
        flash_available = importlib.util.find_spec("flash_attn") is not None
        attn_impl = "flash_attention_2" if (self.use_flash_attn and flash_available) else "sdpa"
        desired_dtype = torch.bfloat16
        
        try:
            self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                model_id,
                dtype=desired_dtype,
                quantization_config=quantization_config,
                device_map="auto",  # CRITICAL: "auto" not self.device
                attn_implementation=attn_impl
            )
        except Exception as e:
            # Fall back to SDPA if flash-attn not available
            if "flash" in str(e).lower():
                logger.info("Flash attention unavailable at runtime, falling back to SDPA")
                self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                    model_id,
                    dtype=desired_dtype,
                    quantization_config=quantization_config,
                    device_map="auto",
                    attn_implementation="sdpa"
                )
            else:
                raise

        # Some model wrappers still default to fp32 even when a dtype kwarg is ignored.
        # For non-quantized loads, ensure we end up in the desired dtype for stable, fast inference.
        if quantization_config is None and getattr(self.model, "dtype", None) != desired_dtype:
            try:
                self.model = self.model.to(desired_dtype)
            except Exception:
                pass

    def _load_internvl_model(self):
        """Load InternVL3-14B model."""
        from transformers import AutoModel, AutoTokenizer

        model_id = "OpenGVLab/InternVL3-14B-448"

        quantization_config = None
        if self.quantization == "8bit":
            from transformers import BitsAndBytesConfig
            quantization_config = BitsAndBytesConfig(load_in_8bit=True)
        elif self.quantization == "4bit":
            from transformers import BitsAndBytesConfig
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16
            )

        desired_dtype = torch.bfloat16

        self.model = AutoModel.from_pretrained(
            model_id,
            dtype=desired_dtype,
            quantization_config=quantization_config,
            trust_remote_code=True,
            device_map="auto"
        )

        self.processor = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=True
        )

    def _init_outlines(self):
        """Initialize Outlines constrained decoding generator."""
        try:
            from outlines import generate
            from outlines.models.transformers import Transformers
            
            logger.info("Initializing Outlines constrained decoding...")
            outlines_model = Transformers(self.model, self.processor)
            self._outlines_generator = generate.json(outlines_model, ICON_LABEL_SCHEMA)
            logger.info("Outlines initialized successfully")
        except ImportError:
            logger.warning(
                "Outlines not installed. Install with: pip install outlines\n"
                "Falling back to unconstrained decoding."
            )
            self.use_constrained_decoding = False

    def _build_prompt(self, candidates: List[Dict]) -> str:
        """
        Build detailed VLM prompt with retrieval context.
        
        Full prompt with calibration guidance for accurate confidence scoring.
        """
        # Format similar icons
        similar_icons = ""
        for i, cand in enumerate(candidates[:5], 1):
            similar_icons += f"""
{i}. {cand['semantic_name']} (similarity: {cand['similarity']:.3f})
   Category: {cand['category']}
   Tags: {', '.join(cand['tags'][:8])}
"""

        prompt = f"""You are an expert icon semantic labeling system. Analyze this icon image and provide structured labeling.

IMPORTANT: This icon is similar to these existing icons in the library:
{similar_icons}

Based on these similar icons and your visual analysis, provide a label for the new icon.

ALLOWED CATEGORIES: {', '.join(ALLOWED_CATEGORIES)}

REQUIREMENTS:
1. canonical: Short semantic name (lowercase, hyphenated, no size suffix)
   - If this icon matches an existing one, use that semantic name
   - Otherwise, create a new descriptive name
   - Examples: "folder", "network-connection", "lock", "warning-triangle"

2. tags: 5-12 descriptive tags
   - Must include relevant tags from similar icons if applicable
   - Add: size-related tags if visible (e.g., "48x48", "32x32")
   - Add: retro/vintage tags if old-style icon
   - Examples: ["folder", "directory", "files", "yellow", "win2k", "retro"]

3. category: ONE of {ALLOWED_CATEGORIES}
   - Choose based on primary purpose
   - Prefer categories used by similar icons

4. description: 1-2 sentence description with use cases
   - Example: "Windows 2000 folder icon. Classic yellow folder design from shell32.dll."

5. confidence: Float 0.0-1.0 indicating labeling confidence
   - 0.9-1.0: Icon clearly matches existing pattern
   - 0.7-0.9: Good match with minor uncertainty
   - 0.5-0.7: Uncertain, may need manual review
   - <0.5: Very uncertain

6. alternates: 2-4 alternative semantic names (if applicable)

OUTPUT FORMAT (strict JSON):
{{
    "canonical": "folder",
    "tags": ["folder", "directory", "files", "yellow", "win2k", "retro", "classic", "48x48"],
    "category": "files",
    "description": "Windows 2000 classic folder icon. Yellow folder design from shell32.dll.",
    "confidence": 0.95,
    "alternates": ["folder-closed", "directory", "file-folder"]
}}

Respond with ONLY the JSON object, no other text."""

        return prompt

    def _parse_vlm_response(self, response_text: str) -> Dict:
        """Parse VLM JSON response with robust extraction."""
        text = response_text.strip()

        # Strip markdown code fences
        if text.startswith('```json'):
            text = text[7:]
        elif text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        text = text.strip()

        # Try to find JSON object in response
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]

        try:
            label_dict = json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse VLM response: {e}")
            logger.error(f"Response: {text[:500]}")
            raise ValueError(f"Invalid JSON from VLM: {e}")

        # Validate required fields
        required = ['canonical', 'tags', 'category', 'description', 'confidence']
        for field in required:
            if field not in label_dict:
                raise ValueError(f"Missing required field: {field}")

        # NOTE: category coercion now happens after parse (so we can use retrieval candidates too).
        # Keep this method focused on JSON extraction + required fields.

        # Ensure alternates exists
        if 'alternates' not in label_dict:
            label_dict['alternates'] = []

        # Clamp confidence
        label_dict['confidence'] = max(0.0, min(1.0, float(label_dict['confidence'])))

        return label_dict

    def _run_inference(self, image: Image.Image, prompt: str) -> str:
        """Run single VLM inference."""
        self._load_model()

        if self.model_name == "qwen2.5-vl-7b":
            return self._run_qwen_inference(image, prompt)
        else:
            return self._run_internvl_inference(image, prompt)

    def _run_qwen_inference(self, image: Image.Image, prompt: str) -> str:
        """Run inference with Qwen2.5-VL."""
        from qwen_vl_utils import process_vision_info
        from transformers import GenerationConfig

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt}
                ]
            }
        ]

        text = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        image_inputs, video_inputs = process_vision_info(messages)

        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt"
        )
        inputs = inputs.to(self.model.device)

        generation_config = GenerationConfig(
            max_new_tokens=512,
            do_sample=False,  # Deterministic for structured output
        )

        with torch.inference_mode():
            generated_ids = self.model.generate(
                **inputs,
                generation_config=generation_config,
            )

        # Trim input tokens
        generated_ids_trimmed = [
            out_ids[len(in_ids):] 
            for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]

        return self.processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]

    def _run_qwen_batch_inference(
        self, 
        images: List[Image.Image], 
        prompts: List[str]
    ) -> List[str]:
        """
        Run batched inference with Qwen2.5-VL.
        
        Native HuggingFace batching - processes multiple images in one forward pass.
        """
        from qwen_vl_utils import process_vision_info
        from transformers import GenerationConfig
        
        if not images:
            return []
        
        # Build message batch
        messages_batch = []
        for img, prompt in zip(images, prompts):
            messages_batch.append([
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": img},
                        {"type": "text", "text": prompt}
                    ]
                }
            ])
        
        # Apply chat template to each
        texts = [
            self.processor.apply_chat_template(
                msgs, tokenize=False, add_generation_prompt=True
            )
            for msgs in messages_batch
        ]
        
        # Process vision info for each
        all_image_inputs = []
        for msgs in messages_batch:
            img_inputs, _ = process_vision_info(msgs)
            all_image_inputs.extend(img_inputs)
        
        # Batch process
        inputs = self.processor(
            text=texts,
            images=all_image_inputs,
            padding=True,
            return_tensors="pt"
        )
        inputs = inputs.to(self.model.device)
        
        generation_config = GenerationConfig(
            max_new_tokens=512,
            do_sample=False,
        )

        with torch.inference_mode():
            generated_ids = self.model.generate(
                **inputs,
                generation_config=generation_config,
            )
        
        # Trim and decode each
        responses = []
        for i, (in_ids, out_ids) in enumerate(zip(inputs.input_ids, generated_ids)):
            trimmed = out_ids[len(in_ids):]
            decoded = self.processor.decode(
                trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False
            )
            responses.append(decoded)
        
        return responses

    def _run_internvl_inference(self, image: Image.Image, prompt: str) -> str:
        """Run inference with InternVL3."""
        temp_path = self.cache_dir / "temp_inference.png"
        image.save(temp_path)

        pixel_values = self.model.load_image(str(temp_path), max_num=6).to(
            torch.bfloat16
        ).to(self.model.device)

        with torch.inference_mode():
            response = self.model.chat(
                self.processor,
                pixel_values,
                prompt,
                generation_config={"max_new_tokens": 512, "do_sample": False}
            )

        temp_path.unlink()
        return response

    def _get_cache_key(self, icon_path: Path) -> str:
        """Generate cache key from file hash."""
        with open(icon_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]

    def _load_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Load cached result."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            with open(cache_file) as f:
                return json.load(f)
        return None

    def _save_to_cache(self, cache_key: str, label_dict: Dict):
        """Save result to cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        with open(cache_file, 'w') as f:
            json.dump(label_dict, f, indent=2)

    def _get_retrieval_candidates(self, icon_path: Path, k: int = 10) -> List[Dict]:
        """Get k-nearest neighbors from catalog."""
        if self.retriever is None:
            return []

        try:
            icon_embedding = self.retriever.embed_image(icon_path)
            return self.retriever.retrieve_for_labeling(
                icon_embedding,
                catalog_path=self.catalog_path,
                k=k,
                mode="projected"
            )
        except ModuleNotFoundError as e:
            logger.warning(f"Retrieval disabled (missing dependency): {e}")
            return []
        except Exception as e:
            logger.warning(f"Retrieval failed for {icon_path.name}: {e}")
            return []

    def _batch_embed_icons(self, icon_paths: List[Path], batch_size: int = 64) -> np.ndarray:
        """
        Batch embed icons through CLIP for efficient retrieval.
        
        Instead of one-at-a-time embedding, processes all icons in batches
        through CLIP vision encoder. 10-50x faster for large batches.
        
        Args:
            icon_paths: List of icon paths to embed
            batch_size: CLIP batch size (64 works well on 24GB VRAM)
            
        Returns:
            Embeddings array of shape (n_icons, d)
        """
        if self.retriever is None:
            return np.array([])

        # Ensure CLIP is loaded (may fail locally if open_clip is not installed)
        try:
            self.retriever._ensure_model_loaded()
        except ModuleNotFoundError as e:
            logger.warning(f"Batch CLIP embedding disabled (missing dependency): {e}")
            return np.array([])
        except Exception as e:
            logger.warning(f"Batch CLIP embedding disabled (failed to init model): {e}")
            return np.array([])
        
        try:
            from iconics_embeddings import normalize_embeddings
        except ModuleNotFoundError as e:
            logger.warning(f"Batch CLIP embedding disabled (missing dependency): {e}")
            return np.array([])

        from PIL import Image
        
        model = self.retriever._model
        preprocess = self.retriever._preprocess
        device = self.retriever._device
        
        all_embeddings = []
        
        for i in range(0, len(icon_paths), batch_size):
            batch_paths = icon_paths[i:i + batch_size]
            batch_tensors = []
            
            for path in batch_paths:
                try:
                    img = Image.open(path).convert("RGB")
                    tensor = preprocess(img).unsqueeze(0)
                    batch_tensors.append(tensor)
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")
                    # Use zero tensor as placeholder
                    batch_tensors.append(torch.zeros(1, 3, 224, 224))
            
            if batch_tensors:
                batch = torch.cat(batch_tensors, dim=0).to(device)
                
                with torch.inference_mode():
                    embeddings = model.encode_image(batch)
                    embeddings = embeddings.cpu().numpy()
                
                embeddings = normalize_embeddings(embeddings)
                all_embeddings.append(embeddings)
        
        return np.vstack(all_embeddings) if all_embeddings else np.array([])

    def label_icon(
        self,
        icon_path: Path,
        use_cache: bool = True,
        k_neighbors: int = 10
    ) -> IconLabel:
        """
        Label a single icon.
        
        Args:
            icon_path: Path to source icon PNG
            use_cache: Use cached result if available
            k_neighbors: Number of retrieval candidates
            
        Returns:
            IconLabel with structured metadata
        """
        icon_path = Path(icon_path)
        if not icon_path.exists():
            raise FileNotFoundError(f"Icon not found: {icon_path}")

        # Check cache
        cache_key = self._get_cache_key(icon_path)
        if use_cache:
            cached = self._load_from_cache(cache_key)
            if cached:
                logger.info(f"Cache hit for {icon_path.name}")
                return IconLabel(**cached)

        # Step 1: Retrieve similar icons (optional)
        logger.info(f"Retrieving similar icons for {icon_path.name}...")
        candidates = self._get_retrieval_candidates(icon_path, k_neighbors)

        # Step 2: HIGH-CONFIDENCE BYPASS
        if candidates and candidates[0]['similarity'] >= self.retrieval_bypass_threshold:
            top = candidates[0]
            logger.info(
                f"High-confidence retrieval match ({top['similarity']:.3f}), "
                f"bypassing VLM: {top['semantic_name']}"
            )
            label_dict = {
                'canonical': top['semantic_name'],
                'tags': top['tags'],
                'category': coerce_category(top.get('category', 'misc'), tags=top.get('tags'), candidates=candidates),
                'description': top.get('description', f"Similar to {top['semantic_name']}"),
                'confidence': float(top['similarity']),
                'alternates': [c['semantic_name'] for c in candidates[1:4]],
                'retrieval_candidates': candidates
            }
            
            if use_cache:
                self._save_to_cache(cache_key, label_dict)
            
            return IconLabel(**label_dict)

        # Step 3: Preprocess icon (4-panel composite)
        logger.info(f"Preprocessing {icon_path.name}...")
        processed_image = preprocess_icon(icon_path)

        # Step 4: Build prompt and run VLM
        prompt = self._build_prompt(candidates)
        logger.info("Running VLM inference...")
        response_text = self._run_inference(processed_image, prompt)

        # Step 5: Parse response
        logger.info("Parsing VLM response...")
        label_dict = self._parse_vlm_response(response_text)
        label_dict["category"] = coerce_category(
            label_dict.get("category", "misc"),
            tags=label_dict.get("tags"),
            candidates=candidates,
        )
        label_dict['retrieval_candidates'] = candidates

        # Cache result
        if use_cache:
            self._save_to_cache(cache_key, label_dict)

        return IconLabel(**label_dict)

    def label_icons_batch(
        self,
        icon_paths: List[Path],
        use_cache: bool = True,
        k_neighbors: int = 10,
        batch_size: int = 4,
        clip_batch_size: int = 64
    ) -> List[IconLabel]:
        """
        Label multiple icons with batched inference.
        
        Optimized pipeline:
        1. Check cache for all icons
        2. Batch embed remaining icons through CLIP (10-50x faster than one-at-a-time)
        3. Batch retrieve k-NN for each
        4. Check retrieval bypass threshold
        5. Batch VLM inference on remaining icons
        
        Args:
            icon_paths: List of icon paths
            use_cache: Use cached results
            k_neighbors: Retrieval candidates per icon
            batch_size: VLM batch size (4-8 recommended for 24GB VRAM)
            clip_batch_size: CLIP batch size for retrieval (64 recommended)
            
        Returns:
            List of IconLabels in same order as input
        """
        results: Dict[int, IconLabel] = {}
        needs_embedding: List[tuple] = []  # (idx, icon_path)

        # First pass: check cache
        for idx, icon_path in enumerate(icon_paths):
            icon_path = Path(icon_path)
            
            if not icon_path.exists():
                logger.warning(f"Icon not found: {icon_path}")
                continue

            cache_key = self._get_cache_key(icon_path)
            if use_cache:
                cached = self._load_from_cache(cache_key)
                if cached:
                    logger.info(f"Cache hit: {icon_path.name}")
                    results[idx] = IconLabel(**cached)
                    continue

            needs_embedding.append((idx, icon_path))

        if not needs_embedding:
            return [results[i] for i in sorted(results.keys())]

        # Second pass: batch CLIP embedding (optional; requires retrieval system)
        paths_to_embed = [p for _, p in needs_embedding]
        embeddings = np.array([])
        if self.retriever is not None:
            logger.info(f"Batch embedding {len(needs_embedding)} icons through CLIP...")
            embeddings = self._batch_embed_icons(paths_to_embed, batch_size=clip_batch_size)
        
        # Third pass: retrieval and bypass check
        pending_vlm: List[tuple] = []  # (idx, icon_path, candidates)
        
        for order, (idx, icon_path) in enumerate(needs_embedding):
            candidates = []

            # Retrieve using pre-computed embedding (if available)
            if self.retriever is not None and embeddings.size:
                try:
                    embedding = embeddings[order]
                    candidates = self.retriever.retrieve_for_labeling(
                        embedding,
                        catalog_path=self.catalog_path,
                        k=k_neighbors,
                        mode="projected"
                    )
                except Exception as e:
                    logger.warning(f"Batch retrieval failed for {icon_path.name}: {e}")
                    candidates = []
            
            # Check retrieval bypass
            if candidates and candidates[0]['similarity'] >= self.retrieval_bypass_threshold:
                top = candidates[0]
                logger.info(f"Retrieval bypass: {icon_path.name} -> {top['semantic_name']}")
                label_dict = {
                    'canonical': top['semantic_name'],
                    'tags': top['tags'],
                    'category': coerce_category(top.get('category', 'misc'), tags=top.get('tags'), candidates=candidates),
                    'description': top.get('description', ''),
                    'confidence': float(top['similarity']),
                    'alternates': [c['semantic_name'] for c in candidates[1:4]],
                    'retrieval_candidates': candidates
                }
                results[idx] = IconLabel(**label_dict)
                if use_cache:
                    cache_key = self._get_cache_key(icon_path)
                    self._save_to_cache(cache_key, label_dict)
                continue

            pending_vlm.append((idx, icon_path, candidates))

        # Fourth pass: batch VLM inference
        if pending_vlm:
            logger.info(f"Running VLM inference on {len(pending_vlm)} icons...")
            self._load_model()

            for batch_start in range(0, len(pending_vlm), batch_size):
                batch = pending_vlm[batch_start:batch_start + batch_size]
                
                # Prepare batch
                batch_images = []
                batch_prompts = []
                for idx, icon_path, candidates in batch:
                    img = preprocess_icon(icon_path)
                    batch_images.append(img)
                    batch_prompts.append(self._build_prompt(candidates))
                
                # Run batch inference
                if self.model_name == "qwen2.5-vl-7b":
                    responses = self._run_qwen_batch_inference(batch_images, batch_prompts)
                else:
                    # InternVL doesn't have great batch support, fall back to sequential
                    responses = [
                        self._run_internvl_inference(img, prompt)
                        for img, prompt in zip(batch_images, batch_prompts)
                    ]

                # Parse responses
                for (idx, icon_path, candidates), response in zip(batch, responses):
                    try:
                        label_dict = self._parse_vlm_response(response)
                        label_dict["category"] = coerce_category(
                            label_dict.get("category", "misc"),
                            tags=label_dict.get("tags"),
                            candidates=candidates,
                        )
                        label_dict['retrieval_candidates'] = candidates
                        results[idx] = IconLabel(**label_dict)

                        if use_cache:
                            cache_key = self._get_cache_key(icon_path)
                            self._save_to_cache(cache_key, label_dict)

                    except Exception as e:
                        logger.error(f"Failed to parse response for {icon_path}: {e}")

        # Return in original order
        return [results[i] for i in sorted(results.keys())]


# Convenience function
def label_icon(
    icon_path: Path,
    model_name: str = "qwen2.5-vl-7b",
    use_cache: bool = True
) -> IconLabel:
    """Standalone function to label a single icon."""
    labeler = VisionLabeler(model_name=model_name)
    return labeler.label_icon(icon_path, use_cache=use_cache)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 iconics_vision.py <icon_path> [--no-cache] [--batch <path2> <path3> ...]")
        sys.exit(1)

    use_cache = "--no-cache" not in sys.argv
    batch_mode = "--batch" in sys.argv
    
    # Filter out flags
    icon_paths = [
        Path(arg) for arg in sys.argv[1:] 
        if not arg.startswith("--")
    ]

    if not icon_paths:
        print("Error: No icon paths provided")
        sys.exit(1)

    for p in icon_paths:
        if not p.exists():
            print(f"Error: Icon not found: {p}")
            sys.exit(1)

    logging.basicConfig(level=logging.INFO)

    labeler = VisionLabeler()
    
    if batch_mode or len(icon_paths) > 1:
        print(f"Batch labeling {len(icon_paths)} icons...")
        labels = labeler.label_icons_batch(icon_paths, use_cache=use_cache)
        
        for icon_path, label in zip(icon_paths, labels):
            print(f"\n{'='*60}")
            print(f"RESULT: {icon_path.name}")
            print(f"{'='*60}")
            print(f"Canonical:   {label.canonical}")
            print(f"Category:    {label.category}")
            print(f"Confidence:  {label.confidence:.3f}")
    else:
        icon_path = icon_paths[0]
        print(f"Labeling: {icon_path}")
        label = labeler.label_icon(icon_path, use_cache=use_cache)

        print(f"\n{'='*60}")
        print("LABELING RESULT")
        print(f"{'='*60}")
        print(f"Canonical:   {label.canonical}")
        print(f"Category:    {label.category}")
        print(f"Tags:        {', '.join(label.tags)}")
        print(f"Description: {label.description}")
        print(f"Confidence:  {label.confidence:.3f}")
        if label.alternates:
            print(f"Alternates:  {', '.join(label.alternates)}")

        print("\nTop 5 Similar Icons:")
        for i, cand in enumerate(label.retrieval_candidates[:5], 1):
            print(f"  {i}. {cand['semantic_name']} (sim: {cand['similarity']:.3f})")
