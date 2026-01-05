#!/usr/bin/env python3
"""
Vision Labeler Evaluation Harness
Tests accuracy against existing catalog icons
"""

import json
import random
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from iconics_vision import VisionLabeler

@dataclass
class EvalResult:
    """Evaluation metrics for a single icon."""
    icon_id: str
    ground_truth_semantic: str
    ground_truth_tags: List[str]
    ground_truth_category: str
    predicted_semantic: str
    predicted_tags: List[str]
    predicted_category: str
    confidence: float
    semantic_exact_match: bool
    semantic_in_alternates: bool
    category_match: bool
    tag_overlap_f1: float

def load_catalog(catalog_path: Path) -> Dict:
    """Load icon catalog."""
    with open(catalog_path) as f:
        return json.load(f)

def sample_icons(catalog: Dict, n: int = 200, seed: int = 42) -> List[Dict]:
    """
    Sample n random icons from catalog for evaluation.

    Args:
        catalog: Full icon catalog
        n: Number of icons to sample
        seed: Random seed for reproducibility

    Returns:
        List of sampled icon entries
    """
    random.seed(seed)
    all_icons = catalog['icons']

    # Filter to icons that exist (have files)
    icons_with_files = [
        icon for icon in all_icons
        if Path(icon['filename']).exists()
    ]

    n = min(n, len(icons_with_files))
    return random.sample(icons_with_files, n)

def compute_tag_f1(ground_truth: List[str], predicted: List[str]) -> float:
    """
    Compute F1 score for tag overlap.

    F1 = 2 * (precision * recall) / (precision + recall)
    where:
        precision = |intersection| / |predicted|
        recall = |intersection| / |ground_truth|
    """
    if not ground_truth and not predicted:
        return 1.0  # Both empty = perfect match

    if not ground_truth or not predicted:
        return 0.0  # One empty, one not = no match

    # Normalize tags (lowercase, strip)
    gt_set = set(tag.lower().strip() for tag in ground_truth)
    pred_set = set(tag.lower().strip() for tag in predicted)

    intersection = gt_set & pred_set

    if not intersection:
        return 0.0

    precision = len(intersection) / len(pred_set)
    recall = len(intersection) / len(gt_set)

    f1 = 2 * (precision * recall) / (precision + recall)
    return f1

def evaluate_icon(
    icon_entry: Dict,
    labeler: VisionLabeler,
    raw_dir: Path
) -> EvalResult:
    """
    Evaluate vision labeler on a single icon.

    Args:
        icon_entry: Ground truth catalog entry
        labeler: Vision labeler instance
        raw_dir: Base directory for icon files

    Returns:
        EvalResult with metrics
    """
    icon_id = icon_entry['id']
    icon_path = raw_dir / icon_entry['filename']

    if not icon_path.exists():
        # Try relative to raw_dir
        icon_path = Path(icon_entry['filename'])
        if not icon_path.exists():
            raise FileNotFoundError(f"Icon not found: {icon_entry['filename']}")

    # Ground truth
    gt_semantic = icon_entry.get('semanticName', icon_id)
    gt_tags = icon_entry.get('tags', [])
    gt_category = icon_entry.get('category', 'unknown')

    # Predict
    label = labeler.label_icon(icon_path, use_cache=False)  # Don't use cache for eval

    # Compute metrics
    semantic_exact = (label.canonical.lower() == gt_semantic.lower())
    semantic_in_alts = any(
        alt.lower() == gt_semantic.lower()
        for alt in label.alternates
    )
    category_match = (label.category == gt_category)
    tag_f1 = compute_tag_f1(gt_tags, label.tags)

    return EvalResult(
        icon_id=icon_id,
        ground_truth_semantic=gt_semantic,
        ground_truth_tags=gt_tags,
        ground_truth_category=gt_category,
        predicted_semantic=label.canonical,
        predicted_tags=label.tags,
        predicted_category=label.category,
        confidence=label.confidence,
        semantic_exact_match=semantic_exact,
        semantic_in_alternates=semantic_in_alts,
        category_match=category_match,
        tag_overlap_f1=tag_f1
    )

def compute_aggregate_metrics(results: List[EvalResult]) -> Dict:
    """
    Compute aggregate evaluation metrics.

    Returns:
        Dict with overall metrics
    """
    n = len(results)

    # Semantic matching
    exact_matches = sum(r.semantic_exact_match for r in results)
    in_top3 = sum(r.semantic_exact_match or r.semantic_in_alternates for r in results)

    # Category matching
    category_matches = sum(r.category_match for r in results)

    # Tag F1
    avg_tag_f1 = sum(r.tag_overlap_f1 for r in results) / n

    # Confidence calibration (Pearson correlation)
    # High confidence should correlate with correct predictions
    confidences = [r.confidence for r in results]
    correctness = [1.0 if r.semantic_exact_match else 0.0 for r in results]

    # Compute Pearson r
    import numpy as np
    if len(set(confidences)) > 1 and len(set(correctness)) > 1:
        correlation = np.corrcoef(confidences, correctness)[0, 1]
    else:
        correlation = 0.0

    # Confidence binning
    high_conf_results = [r for r in results if r.confidence >= 0.7]
    low_conf_results = [r for r in results if r.confidence < 0.7]

    high_conf_accuracy = (
        sum(r.semantic_exact_match for r in high_conf_results) / len(high_conf_results)
        if high_conf_results else 0.0
    )
    low_conf_accuracy = (
        sum(r.semantic_exact_match for r in low_conf_results) / len(low_conf_results)
        if low_conf_results else 0.0
    )

    return {
        'n_samples': n,
        'semantic_exact_match': exact_matches / n,
        'semantic_in_top3': in_top3 / n,
        'category_accuracy': category_matches / n,
        'avg_tag_f1': avg_tag_f1,
        'confidence_correlation': correlation,
        'high_confidence_count': len(high_conf_results),
        'high_confidence_accuracy': high_conf_accuracy,
        'low_confidence_count': len(low_conf_results),
        'low_confidence_accuracy': low_conf_accuracy
    }

def print_results(metrics: Dict, verbose: bool = False):
    """Print evaluation results in human-readable format."""
    print("\n" + "="*60)
    print("VISION LABELER EVALUATION RESULTS")
    print("="*60)
    print(f"\nSample Size: {metrics['n_samples']} icons")

    print("\n--- Semantic Matching ---")
    print(f"Exact Match:     {metrics['semantic_exact_match']*100:.1f}%")
    print(f"In Top-3:        {metrics['semantic_in_top3']*100:.1f}%")

    print("\n--- Category Accuracy ---")
    print(f"Category Match:  {metrics['category_accuracy']*100:.1f}%")

    print("\n--- Tag Overlap ---")
    print(f"Average F1:      {metrics['avg_tag_f1']:.3f}")

    print("\n--- Confidence Calibration ---")
    print(f"Correlation (r): {metrics['confidence_correlation']:.3f}")
    print(f"\nHigh Confidence (>=0.7): {metrics['high_confidence_count']} icons")
    print(f"  Accuracy:      {metrics['high_confidence_accuracy']*100:.1f}%")
    print(f"Low Confidence (<0.7):   {metrics['low_confidence_count']} icons")
    print(f"  Accuracy:      {metrics['low_confidence_accuracy']*100:.1f}%")

    # Pass/Fail criteria (from plan)
    print("\n--- Success Criteria ---")

    criteria = [
        ("Exact Match >70%", metrics['semantic_exact_match'] >= 0.70),
        ("Top-3 Match >90%", metrics['semantic_in_top3'] >= 0.90),
        ("Tag F1 >0.80", metrics['avg_tag_f1'] >= 0.80),
        ("Confidence Corr >0.50", metrics['confidence_correlation'] >= 0.50)
    ]

    for criterion, passed in criteria:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} {criterion}")

    all_passed = all(passed for _, passed in criteria)
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL CRITERIA MET - Vision labeler is production-ready!")
    else:
        print("⚠ Some criteria not met - Consider fine-tuning or manual review")
    print("="*60)

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate vision labeler accuracy against catalog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate on 200 random icons (default)
  python3 scripts/eval_vision_labeler.py

  # Evaluate on 50 icons for quick test
  python3 scripts/eval_vision_labeler.py --sample-size 50

  # Save detailed results to JSON
  python3 scripts/eval_vision_labeler.py --output eval_results.json

  # Use different model
  python3 scripts/eval_vision_labeler.py --model internvl3-14b
        """
    )

    parser.add_argument(
        '--sample-size', '-n',
        type=int,
        default=200,
        help='Number of icons to sample for evaluation (default: 200)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default='qwen2.5-vl-7b',
        choices=['qwen2.5-vl-7b', 'internvl3-14b'],
        help='Vision model to evaluate (default: qwen2.5-vl-7b)'
    )

    parser.add_argument(
        '--catalog',
        type=Path,
        default=Path('icon-catalog.json'),
        help='Path to icon catalog (default: icon-catalog.json)'
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Save detailed results to JSON file'
    )

    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print per-icon results'
    )

    args = parser.parse_args()

    # Load catalog
    print(f"Loading catalog from {args.catalog}...")
    catalog = load_catalog(args.catalog)

    # Sample icons
    print(f"Sampling {args.sample_size} icons for evaluation...")
    sample = sample_icons(catalog, n=args.sample_size, seed=args.seed)
    print(f"Selected {len(sample)} icons")

    # Initialize labeler
    print(f"\nInitializing vision labeler (model: {args.model})...")
    labeler = VisionLabeler(model_name=args.model)

    # Evaluate each icon
    print("\n" + "="*60)
    print("Running evaluation (this may take a while)...")
    print("="*60)

    results = []
    raw_dir = Path.cwd()  # Assume running from iconics root

    for idx, icon_entry in enumerate(sample, 1):
        icon_id = icon_entry['id']
        print(f"\n[{idx}/{len(sample)}] Evaluating {icon_id}")

        try:
            result = evaluate_icon(icon_entry, labeler, raw_dir)
            results.append(result)

            if args.verbose:
                match_str = "✓" if result.semantic_exact_match else "✗"
                print(f"  {match_str} GT: {result.ground_truth_semantic}")
                print(f"     Pred: {result.predicted_semantic} (conf: {result.confidence:.3f})")
                print(f"     Tag F1: {result.tag_overlap_f1:.3f}")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue

    if not results:
        print("\n✗ No results - evaluation failed")
        return 1

    # Compute aggregate metrics
    metrics = compute_aggregate_metrics(results)

    # Print results
    print_results(metrics, verbose=args.verbose)

    # Save detailed results if requested
    if args.output:
        output_data = {
            'metrics': metrics,
            'results': [
                {
                    'icon_id': r.icon_id,
                    'ground_truth': {
                        'semantic': r.ground_truth_semantic,
                        'tags': r.ground_truth_tags,
                        'category': r.ground_truth_category
                    },
                    'predicted': {
                        'semantic': r.predicted_semantic,
                        'tags': r.predicted_tags,
                        'category': r.predicted_category
                    },
                    'confidence': r.confidence,
                    'metrics': {
                        'semantic_exact_match': r.semantic_exact_match,
                        'semantic_in_alternates': r.semantic_in_alternates,
                        'category_match': r.category_match,
                        'tag_f1': r.tag_overlap_f1
                    }
                }
                for r in results
            ]
        }

        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\n✓ Detailed results saved to: {args.output}")

    return 0

if __name__ == '__main__':
    exit(main())
