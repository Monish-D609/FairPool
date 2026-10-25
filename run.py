"""
FairPool: Unified CLI Runner & Entrypoint
Supports starting the web server, executing the deterministic benchmark,
or running the test suite.

Usage:
    python run.py --serve        # Start web application on http://127.0.0.1:8000
    python run.py --benchmark    # Run reproducible scientific benchmark table
    python run.py --test         # Execute pytest test suite
"""

import sys
import os
import argparse
import uvicorn

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def run_benchmark(requests: int = 35, offers: int = 15, seed: int = 42):
    print("=" * 80)
    print("FAIRPOOL: DETERMINISTIC ALGORITHM BENCHMARK HARNESS (FR-21 to FR-25)")
    print(f"Seed: {seed} | Requests: {requests} | Offers: {offers}")
    print("=" * 80)

    from fairpool.simulation.benchmark import BenchmarkHarness
    harness = BenchmarkHarness(seed=seed)
    results = harness.run_single_batch_comparison(
        num_requests=requests, num_offers=offers
    )

    table_md = harness.format_markdown_table(results)
    print("\n" + table_md + "\n")

    print("-" * 80)
    print("Simulating 5-Day Multi-Epoch Fairness Rotation...")
    epoch_study = harness.run_multi_epoch_fairness_study(
        num_epochs=5, requests_per_epoch=requests, num_drivers=offers
    )
    print(f"Initial Day 1 Gini Disparity: {epoch_study['fair_epoch_ginis'][0]}")
    print(f"Final Day 5 Stabilized Gini:  {epoch_study['final_fair_gini']}")
    print(f"Total Cumulative Saved:       {epoch_study['fair_vkm_saved_total']} veh-km")
    print("=" * 80)


def run_tests():
    import pytest
    print("Running FairPool automated test suite...")
    ret = pytest.main(["-v", "tests/"])
    sys.exit(ret)


def start_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    print("=" * 80)
    print("[*] STARTING FAIRPOOL APPLICATION SERVER")
    print(f"URL: http://{host}:{port}")
    print("Access the Bento Box Mobility Dashboard & Interactive Algorithm Visualizer")
    print("=" * 80)
    uvicorn.run("fairpool.api.app:app", host=host, port=port, reload=reload)


def main():
    parser = argparse.ArgumentParser(description="FairPool Unified Entrypoint")
    parser.add_argument("--serve", action="store_true", help="Launch the web server")
    parser.add_argument("--benchmark", action="store_true", help="Run deterministic benchmark suite")
    parser.add_argument("--test", action="store_true", help="Run pytest test suite")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind server (default: 8000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind server")
    parser.add_argument("--requests", type=int, default=35, help="Number of benchmark requests")
    parser.add_argument("--offers", type=int, default=15, help="Number of benchmark driver offers")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")

    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.benchmark:
        run_benchmark(requests=args.requests, offers=args.offers, seed=args.seed)
    else:
        # Default action: serve
        start_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
