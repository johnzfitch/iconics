"""
Unit tests for Iconics Evaluation Framework

Tests all metric implementations against known values and edge cases.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Callable, Dict, List

import numpy as np
import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from iconics_eval import (
    AggregateResults,
    EvaluationResult,
    average_precision,
    compare_methods,
    compute_ranking_vector,
    dcg,
    evaluate_query_set,
    evaluate_single_query,
    f1_at_k,
    format_comparison_table,
    get_first_hit_rank,
    hit_rate_at_k,
    load_ground_truth,
    load_test_queries,
    mrr,
    ndcg,
    precision_at_k,
    recall_at_k,
    save_evaluation_results,
    stratified_sample_ground_truth,
)


# =============================================================================
# MRR Tests
# =============================================================================

class TestMRR:
    """Test Mean Reciprocal Rank implementation."""

    def test_mrr_perfect_ranking(self):
        """First result always relevant -> MRR = 1.0."""
        rankings = [1, 1, 1, 1]
        assert mrr(rankings) == 1.0

    def test_mrr_second_position(self):
        """Relevant always at position 2 -> MRR = 0.5."""
        rankings = [2, 2, 2, 2]
        assert mrr(rankings) == 0.5

    def test_mrr_mixed_positions(self):
        """Mixed positions: (1/1 + 1/2 + 1/5) / 3."""
        rankings = [1, 2, 5]
        expected = (1/1 + 1/2 + 1/5) / 3
        assert abs(mrr(rankings) - expected) < 1e-10

    def test_mrr_no_relevant(self):
        """No relevant results (all zeros) -> MRR = 0.0."""
        rankings = [0, 0, 0]
        assert mrr(rankings) == 0.0

    def test_mrr_empty_list(self):
        """Empty rankings list -> MRR = 0.0."""
        assert mrr([]) == 0.0

    def test_mrr_single_query(self):
        """Single query at position 3 -> MRR = 1/3."""
        rankings = [3]
        assert abs(mrr(rankings) - 1/3) < 1e-10

    def test_mrr_negative_ignored(self):
        """Negative ranks treated as no result."""
        rankings = [-1, 1, 0, 2]
        # Only position 1 and 2 contribute: (1/1 + 1/2) / 4
        expected = (1/1 + 1/2) / 4
        assert abs(mrr(rankings) - expected) < 1e-10


# =============================================================================
# DCG Tests
# =============================================================================

class TestDCG:
    """Test Discounted Cumulative Gain implementation."""

    def test_dcg_basic(self):
        """Basic DCG calculation."""
        relevances = [3, 2, 3, 0, 1, 2]
        # DCG = 3/log2(2) + 2/log2(3) + 3/log2(4) + 0/log2(5) + 1/log2(6) + 2/log2(7)
        expected = 3/1 + 2/np.log2(3) + 3/np.log2(4) + 0/np.log2(5) + 1/np.log2(6) + 2/np.log2(7)
        assert abs(dcg(relevances, 6) - expected) < 1e-10

    def test_dcg_k_cutoff(self):
        """DCG with k cutoff."""
        relevances = [3, 2, 3, 0, 1, 2]
        # Only first 3
        expected = 3/1 + 2/np.log2(3) + 3/np.log2(4)
        assert abs(dcg(relevances, 3) - expected) < 1e-10

    def test_dcg_empty(self):
        """Empty relevances -> DCG = 0."""
        assert dcg([], 5) == 0.0

    def test_dcg_k_zero(self):
        """k=0 -> DCG = 0."""
        assert dcg([1, 2, 3], 0) == 0.0

    def test_dcg_k_larger_than_list(self):
        """k larger than list uses whole list."""
        relevances = [1, 1]
        expected = 1/1 + 1/np.log2(3)
        assert abs(dcg(relevances, 10) - expected) < 1e-10


# =============================================================================
# NDCG Tests
# =============================================================================

class TestNDCG:
    """Test Normalized Discounted Cumulative Gain implementation."""

    def test_ndcg_perfect_ranking(self):
        """Perfect ranking -> NDCG = 1.0."""
        relevances = [3, 2, 1, 0]  # Already ideal order
        assert abs(ndcg(relevances, 4) - 1.0) < 1e-10

    def test_ndcg_worst_ranking(self):
        """Worst ranking (reversed) should be < 1.0."""
        relevances = [0, 1, 2, 3]  # Reversed order
        result = ndcg(relevances, 4)
        assert result < 1.0
        assert result > 0.0

    def test_ndcg_binary_relevance(self):
        """Binary relevance (1s and 0s)."""
        relevances = [1, 0, 1, 0]
        ideal = [1, 1, 0, 0]
        actual_dcg = dcg(relevances, 4)
        ideal_dcg = dcg(ideal, 4)
        expected = actual_dcg / ideal_dcg
        assert abs(ndcg(relevances, 4) - expected) < 1e-10

    def test_ndcg_all_zeros(self):
        """All zeros -> NDCG = 0.0 (no relevant items)."""
        relevances = [0, 0, 0, 0]
        assert ndcg(relevances, 4) == 0.0

    def test_ndcg_empty(self):
        """Empty list -> NDCG = 0.0."""
        assert ndcg([], 5) == 0.0

    def test_ndcg_k_cutoff(self):
        """NDCG respects k cutoff."""
        relevances = [1, 0, 1, 0, 0, 0, 0, 0, 0, 1]  # Relevant at 1, 3, 10
        # At k=5, only positions 1 and 3 matter
        result_k5 = ndcg(relevances, 5)
        result_k10 = ndcg(relevances, 10)
        # Both should be valid NDCG values
        assert 0 <= result_k5 <= 1
        assert 0 <= result_k10 <= 1


# =============================================================================
# Precision@k Tests
# =============================================================================

class TestPrecisionAtK:
    """Test Precision@k implementation."""

    def test_precision_all_relevant(self):
        """All top-k are relevant -> P@k = 1.0."""
        predictions = ['a', 'b', 'c', 'd']
        ground_truth = ['a', 'b', 'c', 'd']
        assert precision_at_k(predictions, ground_truth, 4) == 1.0

    def test_precision_none_relevant(self):
        """None relevant -> P@k = 0.0."""
        predictions = ['a', 'b', 'c', 'd']
        ground_truth = ['x', 'y', 'z']
        assert precision_at_k(predictions, ground_truth, 4) == 0.0

    def test_precision_partial(self):
        """2 of 4 relevant -> P@4 = 0.5."""
        predictions = ['a', 'b', 'c', 'd']
        ground_truth = ['a', 'c', 'e']
        assert precision_at_k(predictions, ground_truth, 4) == 0.5

    def test_precision_at_1(self):
        """P@1 with relevant first."""
        predictions = ['a', 'b', 'c']
        ground_truth = ['a']
        assert precision_at_k(predictions, ground_truth, 1) == 1.0

    def test_precision_at_1_miss(self):
        """P@1 with irrelevant first."""
        predictions = ['b', 'a', 'c']
        ground_truth = ['a']
        assert precision_at_k(predictions, ground_truth, 1) == 0.0

    def test_precision_k_zero(self):
        """k=0 -> P@0 = 0.0."""
        predictions = ['a', 'b']
        ground_truth = ['a']
        assert precision_at_k(predictions, ground_truth, 0) == 0.0

    def test_precision_empty_predictions(self):
        """Empty predictions -> P@k = 0.0."""
        assert precision_at_k([], ['a', 'b'], 5) == 0.0

    def test_precision_empty_ground_truth(self):
        """Empty ground truth -> P@k = 0.0 (nothing relevant)."""
        assert precision_at_k(['a', 'b'], [], 2) == 0.0


# =============================================================================
# Recall@k Tests
# =============================================================================

class TestRecallAtK:
    """Test Recall@k implementation."""

    def test_recall_perfect(self):
        """All relevant found -> R@k = 1.0."""
        predictions = ['a', 'b', 'c', 'd']
        ground_truth = ['a', 'c']
        assert recall_at_k(predictions, ground_truth, 4) == 1.0

    def test_recall_partial(self):
        """1 of 2 relevant found -> R@k = 0.5."""
        predictions = ['a', 'b']
        ground_truth = ['a', 'c']
        assert recall_at_k(predictions, ground_truth, 2) == 0.5

    def test_recall_none_found(self):
        """No relevant found -> R@k = 0.0."""
        predictions = ['x', 'y', 'z']
        ground_truth = ['a', 'b', 'c']
        assert recall_at_k(predictions, ground_truth, 3) == 0.0

    def test_recall_k_cutoff(self):
        """Recall respects k cutoff."""
        predictions = ['a', 'x', 'b', 'c']  # a at 1, b at 3
        ground_truth = ['a', 'b', 'c']
        # At k=2, only 'a' is found (1/3)
        assert abs(recall_at_k(predictions, ground_truth, 2) - 1/3) < 1e-10

    def test_recall_empty_ground_truth(self):
        """Empty ground truth -> R@k = 0.0."""
        assert recall_at_k(['a', 'b'], [], 2) == 0.0

    def test_recall_k_zero(self):
        """k=0 -> R@0 = 0.0."""
        assert recall_at_k(['a', 'b'], ['a'], 0) == 0.0


# =============================================================================
# Average Precision Tests
# =============================================================================

class TestAveragePrecision:
    """Test Average Precision implementation."""

    def test_ap_perfect(self):
        """All relevant at top -> AP = 1.0."""
        predictions = ['a', 'b', 'x', 'y']
        ground_truth = ['a', 'b']
        assert average_precision(predictions, ground_truth) == 1.0

    def test_ap_basic(self):
        """Basic AP calculation."""
        predictions = ['a', 'x', 'b', 'y']
        ground_truth = ['a', 'b']
        # Hit at 1: P@1 = 1.0
        # Hit at 3: P@3 = 2/3
        # AP = (1.0 + 2/3) / 2
        expected = (1.0 + 2/3) / 2
        assert abs(average_precision(predictions, ground_truth) - expected) < 1e-10

    def test_ap_all_at_end(self):
        """All relevant at end."""
        predictions = ['x', 'y', 'a', 'b']
        ground_truth = ['a', 'b']
        # Hit at 3: P@3 = 1/3
        # Hit at 4: P@4 = 2/4
        # AP = (1/3 + 1/2) / 2
        expected = (1/3 + 1/2) / 2
        assert abs(average_precision(predictions, ground_truth) - expected) < 1e-10

    def test_ap_no_relevant(self):
        """No relevant found -> AP = 0.0."""
        predictions = ['x', 'y', 'z']
        ground_truth = ['a', 'b']
        assert average_precision(predictions, ground_truth) == 0.0

    def test_ap_empty_ground_truth(self):
        """Empty ground truth -> AP = 0.0."""
        assert average_precision(['a', 'b'], []) == 0.0

    def test_ap_single_relevant(self):
        """Single relevant item."""
        predictions = ['x', 'a', 'y']
        ground_truth = ['a']
        # Hit at 2: P@2 = 0.5
        # AP = 0.5 / 1
        assert average_precision(predictions, ground_truth) == 0.5


# =============================================================================
# F1@k Tests
# =============================================================================

class TestF1AtK:
    """Test F1@k implementation."""

    def test_f1_perfect(self):
        """Perfect precision and recall -> F1 = 1.0."""
        predictions = ['a', 'b']
        ground_truth = ['a', 'b']
        assert f1_at_k(predictions, ground_truth, 2) == 1.0

    def test_f1_zero(self):
        """No overlap -> F1 = 0.0."""
        predictions = ['x', 'y']
        ground_truth = ['a', 'b']
        assert f1_at_k(predictions, ground_truth, 2) == 0.0

    def test_f1_calculation(self):
        """F1 = 2 * P * R / (P + R)."""
        predictions = ['a', 'x', 'y', 'z']
        ground_truth = ['a', 'b', 'c']
        # P@4 = 1/4, R@4 = 1/3
        p = 1/4
        r = 1/3
        expected = 2 * p * r / (p + r)
        assert abs(f1_at_k(predictions, ground_truth, 4) - expected) < 1e-10


# =============================================================================
# Hit Rate Tests
# =============================================================================

class TestHitRateAtK:
    """Test Hit Rate (Success@k) implementation."""

    def test_hit_at_1_success(self):
        """First item relevant -> hit@1 = 1.0."""
        predictions = ['a', 'b', 'c']
        ground_truth = ['a']
        assert hit_rate_at_k(predictions, ground_truth, 1) == 1.0

    def test_hit_at_1_failure(self):
        """First item not relevant -> hit@1 = 0.0."""
        predictions = ['x', 'a', 'b']
        ground_truth = ['a']
        assert hit_rate_at_k(predictions, ground_truth, 1) == 0.0

    def test_hit_at_k_success(self):
        """Any relevant in top-k -> hit@k = 1.0."""
        predictions = ['x', 'y', 'a', 'z']
        ground_truth = ['a']
        assert hit_rate_at_k(predictions, ground_truth, 4) == 1.0

    def test_hit_at_k_failure(self):
        """No relevant in top-k -> hit@k = 0.0."""
        predictions = ['x', 'y', 'z', 'a']
        ground_truth = ['a']
        assert hit_rate_at_k(predictions, ground_truth, 3) == 0.0

    def test_hit_empty_ground_truth(self):
        """Empty ground truth -> hit = 0.0."""
        assert hit_rate_at_k(['a', 'b'], [], 2) == 0.0


# =============================================================================
# Utility Function Tests
# =============================================================================

class TestUtilityFunctions:
    """Test utility functions."""

    def test_get_first_hit_rank_found(self):
        """First hit at position 2."""
        predictions = ['x', 'a', 'y']
        ground_truth = ['a', 'b']
        assert get_first_hit_rank(predictions, ground_truth) == 2

    def test_get_first_hit_rank_not_found(self):
        """No hit -> rank = 0."""
        predictions = ['x', 'y', 'z']
        ground_truth = ['a', 'b']
        assert get_first_hit_rank(predictions, ground_truth) == 0

    def test_compute_ranking_vector(self):
        """Compute ranks for all ground truth items."""
        predictions = ['a', 'x', 'b', 'y', 'c']
        ground_truth = ['a', 'b', 'c', 'd']
        # a at 1, b at 3, c at 5, d not found
        expected = [1, 3, 5, 0]
        assert compute_ranking_vector(predictions, ground_truth) == expected


# =============================================================================
# Single Query Evaluation Tests
# =============================================================================

class TestEvaluateSingleQuery:
    """Test single query evaluation."""

    def test_evaluate_single_query_perfect(self):
        """Perfect retrieval."""
        def perfect_retriever(q: str, k: int) -> List[str]:
            return ['a', 'b', 'c'][:k]

        result = evaluate_single_query(
            query="test query",
            query_type="literal",
            ground_truth_ids=['a', 'b'],
            retrieve_fn=perfect_retriever,
            k=10
        )

        assert result.query == "test query"
        assert result.query_type == "literal"
        assert result.metrics['mrr'] == 1.0
        assert result.metrics['p@1'] == 1.0
        assert result.retrieved_ids == ['a', 'b', 'c']
        assert result.ground_truth_ids == ['a', 'b']

    def test_evaluate_single_query_partial(self):
        """Partial match."""
        def partial_retriever(q: str, k: int) -> List[str]:
            return ['x', 'a', 'y', 'b'][:k]

        result = evaluate_single_query(
            query="test",
            query_type="conceptual",
            ground_truth_ids=['a', 'b', 'c'],
            retrieve_fn=partial_retriever,
            k=10
        )

        # First relevant at position 2 -> MRR = 0.5
        assert result.metrics['mrr'] == 0.5
        # P@1 = 0 (x not relevant)
        assert result.metrics['p@1'] == 0.0


# =============================================================================
# Aggregate Evaluation Tests
# =============================================================================

class TestEvaluateQuerySet:
    """Test aggregate evaluation over query set."""

    def test_evaluate_query_set_basic(self):
        """Basic query set evaluation."""
        ground_truth = {
            "query1": {"type": "literal", "relevant_ids": ["a", "b"]},
            "query2": {"type": "conceptual", "relevant_ids": ["c", "d"]},
        }

        def mock_retriever(q: str, k: int) -> List[str]:
            if q == "query1":
                return ['a', 'b', 'x']
            else:
                return ['x', 'c', 'y']

        results = evaluate_query_set(ground_truth, mock_retriever, k=10)

        assert results.n_queries == 2
        assert "literal" in results.per_type_metrics
        assert "conceptual" in results.per_type_metrics
        assert results.metrics['mrr'] > 0

    def test_evaluate_query_set_with_individual(self):
        """Query set with individual results."""
        ground_truth = {
            "q1": {"type": "literal", "relevant_ids": ["a"]},
        }

        def mock_retriever(q: str, k: int) -> List[str]:
            return ['a', 'b']

        results = evaluate_query_set(
            ground_truth, mock_retriever, k=10, include_individual=True
        )

        assert len(results.individual_results) == 1
        assert results.individual_results[0].query == "q1"


# =============================================================================
# Method Comparison Tests
# =============================================================================

class TestCompareMethodsAndFormatting:
    """Test method comparison and table formatting."""

    def test_compare_methods(self):
        """Compare two methods."""
        ground_truth = {
            "q1": {"type": "literal", "relevant_ids": ["a"]},
            "q2": {"type": "literal", "relevant_ids": ["b"]},
        }

        def good_method(q: str, k: int) -> List[str]:
            return ['a', 'b', 'c'][:k]

        def bad_method(q: str, k: int) -> List[str]:
            return ['x', 'y', 'z'][:k]

        comparison = compare_methods(
            ground_truth,
            {"good": good_method, "bad": bad_method},
            k=10
        )

        assert "good" in comparison
        assert "bad" in comparison
        assert comparison["good"]["mrr"] > comparison["bad"]["mrr"]

    def test_format_comparison_table(self):
        """Format comparison as table."""
        comparison = {
            "method_a": {"mrr": 0.75, "ndcg@10": 0.80, "p@1": 0.70, "p@5": 0.60, "ap": 0.65},
            "method_b": {"mrr": 0.50, "ndcg@10": 0.55, "p@1": 0.40, "p@5": 0.35, "ap": 0.45},
        }

        table = format_comparison_table(comparison)

        assert "method_a" in table
        assert "method_b" in table
        assert "MRR" in table
        assert "0.750" in table  # method_a MRR


# =============================================================================
# I/O Tests
# =============================================================================

class TestIO:
    """Test file I/O functions."""

    def test_load_ground_truth(self):
        """Load ground truth from JSON."""
        # Create temp file
        data = {
            "queries": [
                {"query": "test1", "type": "literal", "relevant_ids": ["a", "b"]},
                {"query": "test2", "type": "conceptual", "relevant_ids": ["c"]},
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            gt = load_ground_truth(temp_path)
            assert len(gt) == 2
            assert "test1" in gt
            assert gt["test1"]["type"] == "literal"
            assert gt["test1"]["relevant_ids"] == ["a", "b"]
        finally:
            os.unlink(temp_path)

    def test_load_ground_truth_not_found(self):
        """Load from non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_ground_truth("/nonexistent/path.json")

    def test_save_evaluation_results(self):
        """Save evaluation results to JSON."""
        results = AggregateResults(
            metrics={"mrr": 0.8, "p@1": 0.7},
            per_type_metrics={"literal": {"mrr": 0.9}},
            n_queries=10,
            individual_results=[]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "results.json"
            save_evaluation_results(results, path)

            assert path.exists()
            with open(path) as f:
                data = json.load(f)
            assert data["metrics"]["mrr"] == 0.8
            assert data["n_queries"] == 10

    def test_load_test_queries(self):
        """Load test queries from text file."""
        content = """# Comment line
literal: folder icon
conceptual: data organization
emotional: happy confirmation
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            queries = load_test_queries(temp_path)
            assert len(queries) == 3
            assert queries[0] == ("literal", "folder icon")
            assert queries[1] == ("conceptual", "data organization")
        finally:
            os.unlink(temp_path)


# =============================================================================
# Stratified Sampling Tests
# =============================================================================

class TestStratifiedSampling:
    """Test stratified sampling of ground truth."""

    def test_stratified_sample(self):
        """Sample maintains type distribution."""
        ground_truth = {
            f"literal_{i}": {"type": "literal", "relevant_ids": ["a"]}
            for i in range(20)
        }
        ground_truth.update({
            f"conceptual_{i}": {"type": "conceptual", "relevant_ids": ["b"]}
            for i in range(15)
        })

        sampled = stratified_sample_ground_truth(ground_truth, n_per_type=5)

        # Count types
        type_counts = {}
        for info in sampled.values():
            t = info["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        assert type_counts.get("literal", 0) == 5
        assert type_counts.get("conceptual", 0) == 5

    def test_stratified_sample_small_type(self):
        """Sample when type has fewer than n_per_type."""
        ground_truth = {
            "q1": {"type": "rare", "relevant_ids": ["a"]},
            "q2": {"type": "common", "relevant_ids": ["b"]},
            "q3": {"type": "common", "relevant_ids": ["c"]},
            "q4": {"type": "common", "relevant_ids": ["d"]},
        }

        sampled = stratified_sample_ground_truth(ground_truth, n_per_type=10)

        # Should have all items since we can't sample more than exist
        type_counts = {}
        for info in sampled.values():
            t = info["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        assert type_counts.get("rare", 0) == 1  # Only 1 exists
        assert type_counts.get("common", 0) == 3  # Only 3 exist


# =============================================================================
# EvaluationResult and AggregateResults Tests
# =============================================================================

class TestDataclasses:
    """Test dataclass serialization."""

    def test_evaluation_result_to_dict(self):
        """Convert EvaluationResult to dict."""
        result = EvaluationResult(
            query="test",
            query_type="literal",
            metrics={"mrr": 0.5},
            retrieved_ids=["a", "b"],
            ground_truth_ids=["a"]
        )

        d = result.to_dict()
        assert d["query"] == "test"
        assert d["metrics"]["mrr"] == 0.5

    def test_evaluation_result_from_dict(self):
        """Create EvaluationResult from dict."""
        d = {
            "query": "test",
            "query_type": "conceptual",
            "metrics": {"mrr": 0.8},
            "retrieved_ids": ["x"],
            "ground_truth_ids": ["x", "y"]
        }

        result = EvaluationResult.from_dict(d)
        assert result.query == "test"
        assert result.query_type == "conceptual"

    def test_aggregate_results_to_dict(self):
        """Convert AggregateResults to dict."""
        results = AggregateResults(
            metrics={"mrr": 0.7},
            per_type_metrics={"literal": {"mrr": 0.8}},
            n_queries=5,
            individual_results=[]
        )

        d = results.to_dict()
        assert d["n_queries"] == 5
        assert d["metrics"]["mrr"] == 0.7

    def test_aggregate_results_from_dict(self):
        """Create AggregateResults from dict."""
        d = {
            "metrics": {"mrr": 0.6},
            "per_type_metrics": {},
            "n_queries": 10,
            "individual_results": []
        }

        results = AggregateResults.from_dict(d)
        assert results.n_queries == 10


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_predictions_all_metrics(self):
        """All metrics handle empty predictions."""
        predictions = []
        ground_truth = ["a", "b"]

        assert precision_at_k(predictions, ground_truth, 5) == 0.0
        assert recall_at_k(predictions, ground_truth, 5) == 0.0
        assert average_precision(predictions, ground_truth) == 0.0
        assert f1_at_k(predictions, ground_truth, 5) == 0.0
        assert hit_rate_at_k(predictions, ground_truth, 5) == 0.0

    def test_large_k(self):
        """Metrics work with k larger than list."""
        predictions = ["a", "b"]
        ground_truth = ["a", "b", "c"]

        p = precision_at_k(predictions, ground_truth, 100)
        r = recall_at_k(predictions, ground_truth, 100)

        # P@100 = 2/100 = 0.02 (only 2 items in predictions, divided by k=100)
        assert abs(p - 0.02) < 1e-10
        assert abs(r - 2/3) < 1e-10  # 2/3 relevant found

    def test_single_item_lists(self):
        """Metrics work with single-item lists."""
        assert precision_at_k(["a"], ["a"], 1) == 1.0
        assert recall_at_k(["a"], ["a"], 1) == 1.0
        assert average_precision(["a"], ["a"]) == 1.0

    def test_ndcg_with_ties(self):
        """NDCG handles tied relevance scores."""
        relevances = [1, 1, 1, 1]
        # All same relevance, so any order is ideal
        assert ndcg(relevances, 4) == 1.0


# =============================================================================
# Integration with Actual Ground Truth File
# =============================================================================

class TestGroundTruthFile:
    """Test loading the actual ground truth file."""

    def test_load_actual_ground_truth(self):
        """Load the project's ground truth file."""
        gt_path = Path(__file__).parent.parent.parent / "eval" / "ground_truth.json"

        if gt_path.exists():
            gt = load_ground_truth(gt_path)

            # Should have 60+ queries
            assert len(gt) >= 60

            # Check query types
            types = set(info["type"] for info in gt.values())
            expected_types = {"literal", "conceptual", "emotional", "compositional", "negation"}
            assert types == expected_types

            # Check each query has relevant_ids
            for query, info in gt.items():
                assert "relevant_ids" in info
                assert len(info["relevant_ids"]) > 0


class TestTestQueriesFile:
    """Test loading the actual test queries file."""

    def test_load_actual_test_queries(self):
        """Load the project's test queries file."""
        queries_path = Path(__file__).parent.parent.parent / "eval" / "test_queries.txt"

        if queries_path.exists():
            queries = load_test_queries(queries_path)

            # Should have 100+ queries
            assert len(queries) >= 100

            # Check query types
            types = set(q[0] for q in queries)
            expected_types = {"literal", "conceptual", "emotional", "compositional", "negation"}
            assert types == expected_types
