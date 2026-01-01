"""
Iconics Evaluation Framework

This module provides comprehensive evaluation metrics and comparison tools for
the Iconics CLIP-based retrieval system. It implements standard IR metrics and
supports evaluation across different query types.

Key Features:
    - Standard IR metrics: MRR, NDCG, P@k, R@k, MAP
    - Query type categorization: literal, conceptual, emotional, compositional, negation
    - Method comparison: evaluate multiple retrieval approaches side-by-side
    - Ground truth management: load/save evaluation datasets

Mathematical Definitions:
    MRR (Mean Reciprocal Rank):
        MRR = (1/|Q|) * sum(1/rank_i) for each query i
        where rank_i is the position of the first relevant result

    NDCG (Normalized Discounted Cumulative Gain):
        DCG@k = sum(rel_i / log2(i+1)) for i in 1..k
        NDCG@k = DCG@k / IDCG@k
        where IDCG is DCG with ideal (sorted) relevance order

    Precision@k:
        P@k = |relevant in top-k| / k

    Recall@k:
        R@k = |relevant in top-k| / |total relevant|

    Average Precision:
        AP = sum(P@k * rel_k) / |relevant|
        where rel_k is 1 if item at k is relevant, else 0
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class EvaluationResult:
    """
    Container for evaluation results of a single query.

    Attributes:
        query: The query text
        query_type: Category of query (literal, conceptual, emotional,
                   compositional, negation)
        metrics: Dictionary of metric name -> value
        retrieved_ids: List of retrieved icon IDs in order
        ground_truth_ids: List of relevant icon IDs
    """
    query: str
    query_type: str
    metrics: Dict[str, float]
    retrieved_ids: List[str]
    ground_truth_ids: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query": self.query,
            "query_type": self.query_type,
            "metrics": self.metrics,
            "retrieved_ids": self.retrieved_ids,
            "ground_truth_ids": self.ground_truth_ids
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluationResult":
        """Create from dictionary."""
        return cls(
            query=data["query"],
            query_type=data["query_type"],
            metrics=data["metrics"],
            retrieved_ids=data["retrieved_ids"],
            ground_truth_ids=data["ground_truth_ids"]
        )


@dataclass
class AggregateResults:
    """
    Container for aggregate evaluation results across multiple queries.

    Attributes:
        metrics: Aggregate metrics (mean values)
        per_type_metrics: Metrics broken down by query type
        n_queries: Total number of queries evaluated
        individual_results: Optional list of per-query results
    """
    metrics: Dict[str, float]
    per_type_metrics: Dict[str, Dict[str, float]]
    n_queries: int
    individual_results: List[EvaluationResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "metrics": self.metrics,
            "per_type_metrics": self.per_type_metrics,
            "n_queries": self.n_queries,
            "individual_results": [r.to_dict() for r in self.individual_results]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AggregateResults":
        """Create from dictionary."""
        return cls(
            metrics=data["metrics"],
            per_type_metrics=data["per_type_metrics"],
            n_queries=data["n_queries"],
            individual_results=[
                EvaluationResult.from_dict(r)
                for r in data.get("individual_results", [])
            ]
        )


# =============================================================================
# Core Metric Functions
# =============================================================================

def mrr(rankings: List[int]) -> float:
    """
    Compute Mean Reciprocal Rank.

    MRR measures the average of reciprocal ranks of the first relevant result.
    Higher is better; 1.0 means perfect (first result always relevant).

    Args:
        rankings: List of positions where ground truth items appear (1-indexed).
                 Each entry is the rank of the first relevant result for a query.
                 Use 0 or negative to indicate no relevant result found.

    Returns:
        MRR score in [0, 1]. Returns 0.0 if rankings is empty.

    Example:
        >>> mrr([1, 2, 5])  # First relevant at positions 1, 2, 5
        0.5666...  # = (1/1 + 1/2 + 1/5) / 3
        >>> mrr([1, 1, 1])  # Always first
        1.0
        >>> mrr([0, 0, 0])  # Never found
        0.0
    """
    if not rankings:
        return 0.0

    reciprocal_sum = 0.0
    for rank in rankings:
        if rank > 0:
            reciprocal_sum += 1.0 / rank

    return reciprocal_sum / len(rankings)


def dcg(relevances: List[float], k: int) -> float:
    """
    Compute Discounted Cumulative Gain at k.

    DCG weights relevance by position, with logarithmic decay.

    Args:
        relevances: Relevance scores in retrieved order
        k: Cutoff position

    Returns:
        DCG@k score (unbounded, depends on relevance scale)

    Example:
        >>> dcg([3, 2, 3, 0, 1, 2], k=6)
        6.861...
    """
    if not relevances or k <= 0:
        return 0.0

    dcg_score = 0.0
    for i, rel in enumerate(relevances[:k]):
        # Position is 1-indexed in the formula
        position = i + 1
        dcg_score += rel / np.log2(position + 1)

    return dcg_score


def ndcg(relevances: List[float], k: int) -> float:
    """
    Compute Normalized Discounted Cumulative Gain at k.

    NDCG normalizes DCG by the ideal DCG (sorted relevances).
    Returns value in [0, 1], where 1.0 is perfect ranking.

    Args:
        relevances: Relevance scores in retrieved order
        k: Cutoff position

    Returns:
        NDCG@k score in [0, 1]. Returns 0.0 if no relevant items.

    Example:
        >>> ndcg([3, 2, 3, 0, 1, 2], k=6)  # Actual order
        0.961...
        >>> ndcg([3, 3, 2, 2, 1, 0], k=6)  # Ideal order
        1.0
    """
    if not relevances or k <= 0:
        return 0.0

    # Compute actual DCG
    actual_dcg = dcg(relevances, k)

    # Compute ideal DCG (sorted descending)
    ideal_relevances = sorted(relevances, reverse=True)
    ideal_dcg = dcg(ideal_relevances, k)

    if ideal_dcg == 0:
        return 0.0

    return actual_dcg / ideal_dcg


def precision_at_k(predictions: List[str], ground_truth: List[str], k: int) -> float:
    """
    Compute Precision at k.

    Precision@k = (# relevant in top-k) / k

    Args:
        predictions: List of predicted/retrieved icon IDs in order
        ground_truth: List of relevant icon IDs (order doesn't matter)
        k: Cutoff position

    Returns:
        Precision@k in [0, 1]. Returns 0.0 if k <= 0.

    Example:
        >>> precision_at_k(['a', 'b', 'c', 'd'], ['a', 'c', 'e'], k=4)
        0.5  # 2 relevant (a, c) out of 4
        >>> precision_at_k(['a', 'b', 'c', 'd'], ['a', 'c', 'e'], k=2)
        0.5  # 1 relevant (a) out of 2
    """
    if k <= 0:
        return 0.0

    gt_set = set(ground_truth)
    top_k = predictions[:k]

    relevant_count = sum(1 for item in top_k if item in gt_set)

    return relevant_count / k


def recall_at_k(predictions: List[str], ground_truth: List[str], k: int) -> float:
    """
    Compute Recall at k.

    Recall@k = (# relevant in top-k) / (# total relevant)

    Args:
        predictions: List of predicted/retrieved icon IDs in order
        ground_truth: List of relevant icon IDs (order doesn't matter)
        k: Cutoff position

    Returns:
        Recall@k in [0, 1]. Returns 0.0 if no ground truth items.

    Example:
        >>> recall_at_k(['a', 'b', 'c', 'd'], ['a', 'c', 'e'], k=4)
        0.666...  # 2 relevant (a, c) out of 3 total relevant
        >>> recall_at_k(['a', 'b', 'c', 'd'], ['a', 'c', 'e'], k=2)
        0.333...  # 1 relevant (a) out of 3 total relevant
    """
    if not ground_truth or k <= 0:
        return 0.0

    gt_set = set(ground_truth)
    top_k = predictions[:k]

    relevant_count = sum(1 for item in top_k if item in gt_set)

    return relevant_count / len(gt_set)


def average_precision(predictions: List[str], ground_truth: List[str]) -> float:
    """
    Compute Average Precision for ranking evaluation.

    AP = sum(P@k * rel_k) / |relevant|

    where P@k is precision at k, and rel_k is 1 if the k-th item is relevant.

    Args:
        predictions: List of predicted/retrieved icon IDs in order
        ground_truth: List of relevant icon IDs (order doesn't matter)

    Returns:
        Average Precision in [0, 1]. Returns 0.0 if no ground truth items.

    Example:
        >>> average_precision(['a', 'b', 'c', 'd'], ['a', 'c'])
        0.75  # P@1=1.0 (hit), P@3=0.666 (hit) -> (1.0 + 0.666)/2
    """
    if not ground_truth:
        return 0.0

    gt_set = set(ground_truth)
    precisions = []
    relevant_count = 0

    for k, item in enumerate(predictions, start=1):
        if item in gt_set:
            relevant_count += 1
            precisions.append(relevant_count / k)

    if not precisions:
        return 0.0

    return sum(precisions) / len(gt_set)


def f1_at_k(predictions: List[str], ground_truth: List[str], k: int) -> float:
    """
    Compute F1 score at k (harmonic mean of precision and recall).

    Args:
        predictions: List of predicted/retrieved icon IDs in order
        ground_truth: List of relevant icon IDs
        k: Cutoff position

    Returns:
        F1@k in [0, 1]. Returns 0.0 if both precision and recall are 0.
    """
    p = precision_at_k(predictions, ground_truth, k)
    r = recall_at_k(predictions, ground_truth, k)

    if p + r == 0:
        return 0.0

    return 2 * p * r / (p + r)


def hit_rate_at_k(predictions: List[str], ground_truth: List[str], k: int) -> float:
    """
    Compute hit rate (success@k): 1 if any relevant item in top-k, else 0.

    Also known as "success@k" or "hit@k".

    Args:
        predictions: List of predicted/retrieved icon IDs in order
        ground_truth: List of relevant icon IDs
        k: Cutoff position

    Returns:
        1.0 if any ground truth item appears in top-k, else 0.0
    """
    if not ground_truth or k <= 0:
        return 0.0

    gt_set = set(ground_truth)
    top_k = predictions[:k]

    return 1.0 if any(item in gt_set for item in top_k) else 0.0


# =============================================================================
# Single Query Evaluation
# =============================================================================

def evaluate_single_query(
    query: str,
    query_type: str,
    ground_truth_ids: List[str],
    retrieve_fn: Callable[[str, int], List[str]],
    k: int = 10
) -> EvaluationResult:
    """
    Evaluate retrieval performance for a single query.

    Computes all standard metrics for the given query and ground truth.

    Args:
        query: The query text
        query_type: Category of query (literal, conceptual, etc.)
        ground_truth_ids: List of relevant icon IDs
        retrieve_fn: Function(query, k) -> List[icon_ids]
                    Returns list of retrieved icon IDs
        k: Maximum number of results to evaluate

    Returns:
        EvaluationResult containing all metrics

    Example:
        >>> def my_retriever(q, k):
        ...     return retriever.retrieve(q, k=k)
        >>> result = evaluate_single_query(
        ...     "folder icon",
        ...     "literal",
        ...     ["folder-32x32", "folder-48x48"],
        ...     my_retriever,
        ...     k=10
        ... )
        >>> print(result.metrics)
        {'mrr': 1.0, 'ndcg@10': 0.95, 'p@1': 1.0, ...}
    """
    # Retrieve results
    retrieved_ids = retrieve_fn(query, k)

    # Compute first relevant rank for MRR
    gt_set = set(ground_truth_ids)
    first_relevant_rank = 0
    for i, icon_id in enumerate(retrieved_ids, start=1):
        if icon_id in gt_set:
            first_relevant_rank = i
            break

    # Compute relevances for NDCG (binary: 1 if relevant, 0 if not)
    relevances = [1.0 if icon_id in gt_set else 0.0 for icon_id in retrieved_ids]

    # Compute all metrics
    metrics = {
        "mrr": 1.0 / first_relevant_rank if first_relevant_rank > 0 else 0.0,
        "ndcg@10": ndcg(relevances, min(k, 10)),
        "ndcg@5": ndcg(relevances, min(k, 5)),
        "p@1": precision_at_k(retrieved_ids, ground_truth_ids, 1),
        "p@3": precision_at_k(retrieved_ids, ground_truth_ids, 3),
        "p@5": precision_at_k(retrieved_ids, ground_truth_ids, 5),
        "p@10": precision_at_k(retrieved_ids, ground_truth_ids, min(k, 10)),
        "r@5": recall_at_k(retrieved_ids, ground_truth_ids, 5),
        "r@10": recall_at_k(retrieved_ids, ground_truth_ids, min(k, 10)),
        "ap": average_precision(retrieved_ids, ground_truth_ids),
        "hit@1": hit_rate_at_k(retrieved_ids, ground_truth_ids, 1),
        "hit@5": hit_rate_at_k(retrieved_ids, ground_truth_ids, 5),
        "hit@10": hit_rate_at_k(retrieved_ids, ground_truth_ids, min(k, 10)),
        "f1@5": f1_at_k(retrieved_ids, ground_truth_ids, 5),
        "f1@10": f1_at_k(retrieved_ids, ground_truth_ids, min(k, 10)),
    }

    return EvaluationResult(
        query=query,
        query_type=query_type,
        metrics=metrics,
        retrieved_ids=retrieved_ids,
        ground_truth_ids=ground_truth_ids
    )


# =============================================================================
# Aggregate Evaluation
# =============================================================================

def evaluate_query_set(
    ground_truth: Dict[str, Dict],
    retrieve_fn: Callable[[str, int], List[str]],
    k: int = 10,
    include_individual: bool = False
) -> AggregateResults:
    """
    Evaluate over an entire test set.

    Computes aggregate metrics across all queries, as well as
    metrics broken down by query type.

    Args:
        ground_truth: Dictionary mapping query -> {type, relevant_ids}
                     Format: {"folder icon": {"type": "literal",
                              "relevant_ids": ["folder-32x32", ...]}}
        retrieve_fn: Function(query, k) -> List[icon_ids]
        k: Maximum number of results to evaluate
        include_individual: If True, include per-query results in output

    Returns:
        AggregateResults containing:
        - metrics: Overall mean metrics (MRR, NDCG@10, P@1, P@5, P@10, MAP)
        - per_type_metrics: Metrics broken down by query type
        - n_queries: Number of queries evaluated
        - individual_results: Per-query results (if include_individual=True)

    Example:
        >>> gt = {
        ...     "folder icon": {"type": "literal", "relevant_ids": ["folder-32x32"]},
        ...     "data organization": {"type": "conceptual", "relevant_ids": ["folder-32x32", "database-48x48"]}
        ... }
        >>> results = evaluate_query_set(gt, my_retriever)
        >>> print(results.metrics)
        {'mrr': 0.85, 'ndcg@10': 0.78, 'p@1': 0.75, ...}
    """
    all_results: List[EvaluationResult] = []
    type_results: Dict[str, List[EvaluationResult]] = {}

    for query, info in ground_truth.items():
        query_type = info.get("type", "unknown")
        relevant_ids = info.get("relevant_ids", [])

        result = evaluate_single_query(
            query=query,
            query_type=query_type,
            ground_truth_ids=relevant_ids,
            retrieve_fn=retrieve_fn,
            k=k
        )

        all_results.append(result)

        if query_type not in type_results:
            type_results[query_type] = []
        type_results[query_type].append(result)

    # Aggregate overall metrics
    metrics = _aggregate_metrics([r.metrics for r in all_results])

    # Aggregate per-type metrics
    per_type_metrics = {}
    for query_type, results in type_results.items():
        per_type_metrics[query_type] = _aggregate_metrics(
            [r.metrics for r in results]
        )

    return AggregateResults(
        metrics=metrics,
        per_type_metrics=per_type_metrics,
        n_queries=len(all_results),
        individual_results=all_results if include_individual else []
    )


def _aggregate_metrics(metric_dicts: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Aggregate metrics by computing mean across queries.

    Args:
        metric_dicts: List of metric dictionaries

    Returns:
        Dictionary with mean values for each metric
    """
    if not metric_dicts:
        return {}

    # Get all metric names
    all_keys = set()
    for m in metric_dicts:
        all_keys.update(m.keys())

    # Compute mean for each metric
    aggregated = {}
    for key in all_keys:
        values = [m.get(key, 0.0) for m in metric_dicts]
        aggregated[key] = float(np.mean(values))

    return aggregated


# =============================================================================
# Method Comparison
# =============================================================================

def compare_methods(
    ground_truth: Dict[str, Dict],
    methods: Dict[str, Callable[[str, int], List[str]]],
    k: int = 10
) -> Dict[str, Dict[str, float]]:
    """
    Compare multiple retrieval methods on the same ground truth.

    Useful for evaluating different retrieval modes (raw, projected, weighted)
    or comparing different parameter settings.

    Args:
        ground_truth: Dictionary mapping query -> {type, relevant_ids}
        methods: Dictionary mapping method_name -> retrieve_fn
        k: Maximum number of results to evaluate

    Returns:
        Dictionary mapping method_name -> {metric: value}

    Example:
        >>> methods = {
        ...     "raw": lambda q, k: retriever.retrieve(q, k=k, mode="raw"),
        ...     "projected": lambda q, k: retriever.retrieve(q, k=k, mode="projected")
        ... }
        >>> comparison = compare_methods(ground_truth, methods)
        >>> print(comparison)
        {'raw': {'mrr': 0.72, ...}, 'projected': {'mrr': 0.85, ...}}
    """
    results = {}

    for method_name, retrieve_fn in methods.items():
        logger.info(f"Evaluating method: {method_name}")
        agg = evaluate_query_set(ground_truth, retrieve_fn, k=k)
        results[method_name] = agg.metrics

    return results


def format_comparison_table(
    comparison: Dict[str, Dict[str, float]],
    metrics: Optional[List[str]] = None
) -> str:
    """
    Format comparison results as a readable table.

    Args:
        comparison: Output from compare_methods()
        metrics: List of metrics to include. If None, uses default set.

    Returns:
        Formatted string table

    Example:
        >>> print(format_comparison_table(comparison))
        Method     | MRR   | NDCG@10 | P@1   | P@5   | MAP
        -----------+-------+---------+-------+-------+------
        raw        | 0.720 | 0.654   | 0.650 | 0.420 | 0.580
        projected  | 0.850 | 0.782   | 0.800 | 0.560 | 0.710
    """
    if metrics is None:
        metrics = ["mrr", "ndcg@10", "p@1", "p@5", "ap"]

    # Build header
    header = "Method".ljust(15) + " | " + " | ".join(
        m.upper().center(7) for m in metrics
    )
    separator = "-" * 15 + "-+-" + "-+-".join("-" * 7 for _ in metrics)

    # Build rows
    rows = []
    for method_name, method_metrics in sorted(comparison.items()):
        values = [f"{method_metrics.get(m, 0.0):.3f}".center(7) for m in metrics]
        row = method_name.ljust(15) + " | " + " | ".join(values)
        rows.append(row)

    return "\n".join([header, separator] + rows)


# =============================================================================
# I/O Functions
# =============================================================================

def load_ground_truth(path: Union[str, Path]) -> Dict[str, Dict]:
    """
    Load ground truth from JSON file.

    Expected format:
    {
        "queries": [
            {
                "query": "folder icon",
                "type": "literal",
                "relevant_ids": ["folder-32x32", "folder-48x48"]
            },
            ...
        ]
    }

    Args:
        path: Path to ground truth JSON file

    Returns:
        Dictionary mapping query -> {type, relevant_ids}

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
        KeyError: If required fields are missing
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Convert list format to dictionary format
    ground_truth = {}
    for item in data.get("queries", []):
        query = item["query"]
        ground_truth[query] = {
            "type": item.get("type", "unknown"),
            "relevant_ids": item.get("relevant_ids", [])
        }

    logger.info(f"Loaded {len(ground_truth)} queries from {path}")
    return ground_truth


def save_evaluation_results(results: Union[AggregateResults, Dict], path: Union[str, Path]) -> None:
    """
    Save evaluation results to JSON file.

    Args:
        results: Either AggregateResults object or raw dictionary
        path: Path to output JSON file

    Raises:
        IOError: If file cannot be written
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(results, AggregateResults):
        data = results.to_dict()
    else:
        data = results

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved evaluation results to {path}")


def load_test_queries(path: Union[str, Path]) -> List[Tuple[str, str]]:
    """
    Load test queries from text file.

    Expected format (one query per line):
        type: query text
        literal: folder icon
        conceptual: data organization

    Args:
        path: Path to test queries file

    Returns:
        List of (query_type, query_text) tuples
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Test queries file not found: {path}")

    queries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if ":" in line:
                query_type, query_text = line.split(":", 1)
                queries.append((query_type.strip(), query_text.strip()))
            else:
                # Default to unknown type
                queries.append(("unknown", line))

    logger.info(f"Loaded {len(queries)} test queries from {path}")
    return queries


# =============================================================================
# Utility Functions
# =============================================================================

def create_retrieve_fn_from_retriever(retriever, mode: str = "projected"):
    """
    Create a retrieve function compatible with evaluation from IconicsRetriever.

    Args:
        retriever: IconicsRetriever instance
        mode: Retrieval mode ("raw", "projected", "weighted")

    Returns:
        Function(query, k) -> List[icon_ids]
    """
    def retrieve_fn(query: str, k: int) -> List[str]:
        results = retriever.retrieve(query, k=k, mode=mode)
        return [r.icon_id for r in results]

    return retrieve_fn


def get_first_hit_rank(
    predictions: List[str],
    ground_truth: List[str]
) -> int:
    """
    Get the rank of the first relevant item (1-indexed).

    Args:
        predictions: Retrieved items in order
        ground_truth: Relevant items

    Returns:
        Rank of first hit (1-indexed), or 0 if no hit
    """
    gt_set = set(ground_truth)
    for i, item in enumerate(predictions, start=1):
        if item in gt_set:
            return i
    return 0


def compute_ranking_vector(
    predictions: List[str],
    ground_truth: List[str]
) -> List[int]:
    """
    Compute ranking positions of all ground truth items.

    Args:
        predictions: Retrieved items in order
        ground_truth: Relevant items

    Returns:
        List of ranks (1-indexed) for each ground truth item.
        Items not in predictions get rank 0.
    """
    pred_ranks = {item: i + 1 for i, item in enumerate(predictions)}
    return [pred_ranks.get(gt, 0) for gt in ground_truth]


def stratified_sample_ground_truth(
    ground_truth: Dict[str, Dict],
    n_per_type: int = 10,
    seed: int = 42
) -> Dict[str, Dict]:
    """
    Sample ground truth queries stratified by type.

    Useful for creating smaller evaluation sets that maintain
    type distribution.

    Args:
        ground_truth: Full ground truth dictionary
        n_per_type: Number of queries to sample per type
        seed: Random seed for reproducibility

    Returns:
        Sampled ground truth dictionary
    """
    np.random.seed(seed)

    # Group by type
    by_type: Dict[str, List[Tuple[str, Dict]]] = {}
    for query, info in ground_truth.items():
        query_type = info.get("type", "unknown")
        if query_type not in by_type:
            by_type[query_type] = []
        by_type[query_type].append((query, info))

    # Sample from each type
    sampled = {}
    for query_type, queries in by_type.items():
        n_sample = min(n_per_type, len(queries))
        indices = np.random.choice(len(queries), size=n_sample, replace=False)
        for idx in indices:
            query, info = queries[idx]
            sampled[query] = info

    return sampled


def print_evaluation_summary(results: AggregateResults) -> None:
    """
    Print a formatted summary of evaluation results.

    Args:
        results: AggregateResults object
    """
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"\nTotal queries evaluated: {results.n_queries}")

    print("\nOverall Metrics:")
    print("-" * 40)
    for metric, value in sorted(results.metrics.items()):
        print(f"  {metric:12s}: {value:.4f}")

    print("\nMetrics by Query Type:")
    print("-" * 40)
    for query_type, metrics in sorted(results.per_type_metrics.items()):
        print(f"\n  {query_type}:")
        for metric, value in sorted(metrics.items()):
            if metric in ["mrr", "ndcg@10", "p@1", "ap"]:
                print(f"    {metric:12s}: {value:.4f}")

    print("\n" + "=" * 60)
