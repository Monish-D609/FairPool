"""
Unit tests for deterministic reproducibility and NFR-1 performance requirements.
"""

import pytest
import time
from fairpool.simulation.benchmark import BenchmarkHarness


def test_deterministic_benchmark_reproducibility():
    """Verify that identical random seed produces identical match results (FR-24)."""
    harness1 = BenchmarkHarness(seed=99)
    res1 = harness1.run_single_batch_comparison(num_requests=25, num_offers=12)

    harness2 = BenchmarkHarness(seed=99)
    res2 = harness2.run_single_batch_comparison(num_requests=25, num_offers=12)

    assert abs(res1["fairpool_fairness"].total_vkm_saved - res2["fairpool_fairness"].total_vkm_saved) < 1e-4
    assert res1["fairpool_fairness"].match_rate_percent == res2["fairpool_fairness"].match_rate_percent
    assert res1["greedy"].match_rate_percent == res2["greedy"].match_rate_percent


def test_nfr1_performance_scale():
    """
    NFR-1 requirement:
    Batch of up to 100 requests matched within 10 seconds using the approximate solver.
    """
    harness = BenchmarkHarness(seed=42)
    start = time.perf_counter()
    res = harness.run_single_batch_comparison(num_requests=100, num_offers=35)
    elapsed = time.perf_counter() - start

    assert elapsed < 10.0, f"Batch execution took {elapsed:.2f}s, exceeding 10s budget"
    # FairPool should significantly outperform greedy on distance saved
    fair_saved = res["fairpool_fairness"].total_vkm_saved
    greedy_saved = res["greedy"].total_vkm_saved
    assert fair_saved > greedy_saved
