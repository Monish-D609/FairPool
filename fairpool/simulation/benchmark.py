"""
FairPool: Reproducible Benchmark Harness & Multi-Epoch Simulator
Evaluates algorithms against identical datasets under controlled seeds (FR-21 to FR-25).
"""

from __future__ import annotations
import copy
import json
from typing import List, Dict, Any, Optional
from fairpool.core.models import RiderRequest, DriverOffer, BatchMatchResult
from fairpool.core.graph import RoadNetwork, create_default_campus_network
from fairpool.algorithms.baselines import NoPoolingBaseline, GreedyNearestPairMatcher
from fairpool.algorithms.fairness import FairnessEngine
from fairpool.algorithms.engine import FairPoolEngine
from fairpool.simulation.generator import CommuterDatasetGenerator


class BenchmarkHarness:
    """
    Scientific benchmark harness for DAA evaluation.
    Executes all matching algorithms on the exact same requests and offers.
    """

    def __init__(self, road_net: Optional[RoadNetwork] = None, seed: int = 42):
        self.road_net = road_net or create_default_campus_network()
        self.seed = seed
        self.generator = CommuterDatasetGenerator(self.road_net, seed=seed)

    def run_single_batch_comparison(
        self,
        num_requests: int = 50,
        num_offers: int = 25,
        commute_direction: str = "INBOUND",
    ) -> Dict[str, BatchMatchResult]:
        """Runs all 4 algorithms on identical batch input."""
        requests, offers = self.generator.generate_commute_batch(
            num_requests=num_requests,
            num_offers=num_offers,
            commute_direction=commute_direction,
        )

        results: Dict[str, BatchMatchResult] = {}

        # 1. No Pooling
        no_pool = NoPoolingBaseline(self.road_net)
        results["no_pool"] = no_pool.run(
            copy.deepcopy(requests), copy.deepcopy(offers)
        )

        # 2. Greedy Nearest Pair Matcher
        greedy = GreedyNearestPairMatcher(self.road_net)
        results["greedy"] = greedy.run(
            copy.deepcopy(requests), copy.deepcopy(offers)
        )

        # 3. FairPool without Fairness (Ablation)
        fairpool_ablation = FairPoolEngine(
            self.road_net,
            enable_fairness=False,
            use_exact_solver=False,
        )
        results["fairpool_no_fairness"] = fairpool_ablation.match_batch(
            copy.deepcopy(requests), copy.deepcopy(offers), batch_id="ablation_batch"
        )

        # 4. FairPool with Dynamic Fairness
        fairpool_fair = FairPoolEngine(
            self.road_net,
            enable_fairness=True,
            use_exact_solver=False,
        )
        results["fairpool_fairness"] = fairpool_fair.match_batch(
            copy.deepcopy(requests), copy.deepcopy(offers), batch_id="fair_batch"
        )

        return results

    def run_multi_epoch_fairness_study(
        self, num_epochs: int = 5, requests_per_epoch: int = 40, num_drivers: int = 20
    ) -> Dict[str, Any]:
        """
        Simulates consecutive daily commute epochs to measure how fairness
        stabilizes and rotates detours across drivers over time.
        """
        # Persistent driver cohort
        permanent_drivers: List[DriverOffer] = []
        gen = CommuterDatasetGenerator(self.road_net, seed=self.seed)
        _, sample_offers = gen.generate_commute_batch(num_requests=10, num_offers=num_drivers)
        for i, off in enumerate(sample_offers):
            off.driver_id = f"driver_perm_{i+1:02d}"
            permanent_drivers.append(off)

        # Engine with fairness
        fair_ledger = FairnessEngine(enable_fairness=True, fairness_weight=0.5)
        engine_fair = FairPoolEngine(self.road_net, fairness_engine=fair_ledger, enable_fairness=True)

        # Engine without fairness
        unfair_ledger = FairnessEngine(enable_fairness=False)
        engine_unfair = FairPoolEngine(self.road_net, fairness_engine=unfair_ledger, enable_fairness=False)

        fair_epoch_ginis: List[float] = []
        unfair_epoch_ginis: List[float] = []
        fair_vkm_saved_total = 0.0
        unfair_vkm_saved_total = 0.0

        for epoch in range(num_epochs):
            # Generate daily requests
            daily_reqs, _ = gen.generate_commute_batch(
                num_requests=requests_per_epoch, num_offers=num_drivers
            )

            # Daily driver offers with accumulated historical detours
            daily_offers_fair = copy.deepcopy(permanent_drivers)
            for off in daily_offers_fair:
                off.cumulative_detour_min = fair_ledger.driver_cumulative_detours.get(off.driver_id, 0.0)

            daily_offers_unfair = copy.deepcopy(permanent_drivers)
            for off in daily_offers_unfair:
                off.cumulative_detour_min = unfair_ledger.driver_cumulative_detours.get(off.driver_id, 0.0)

            # Run matches
            res_fair = engine_fair.match_batch(
                copy.deepcopy(daily_reqs), daily_offers_fair, batch_id=f"epoch_fair_{epoch+1}"
            )
            res_unfair = engine_unfair.match_batch(
                copy.deepcopy(daily_reqs), daily_offers_unfair, batch_id=f"epoch_unfair_{epoch+1}"
            )

            fair_vkm_saved_total += res_fair.total_vkm_saved
            unfair_vkm_saved_total += res_unfair.total_vkm_saved

            fair_epoch_ginis.append(fair_ledger.get_cohort_gini())
            unfair_epoch_ginis.append(unfair_ledger.get_cohort_gini())

        return {
            "num_epochs": num_epochs,
            "num_drivers": num_drivers,
            "requests_per_epoch": requests_per_epoch,
            "fair_epoch_ginis": [round(g, 4) for g in fair_epoch_ginis],
            "unfair_epoch_ginis": [round(g, 4) for g in unfair_epoch_ginis],
            "fair_vkm_saved_total": round(fair_vkm_saved_total, 2),
            "unfair_vkm_saved_total": round(unfair_vkm_saved_total, 2),
            "final_fair_gini": round(fair_ledger.get_cohort_gini(), 4),
            "final_unfair_gini": round(unfair_ledger.get_cohort_gini(), 4),
        }

    def format_markdown_table(self, results: Dict[str, BatchMatchResult]) -> str:
        """Formats single batch benchmark results as a clean Markdown comparison table."""
        headers = [
            "Algorithm",
            "Matched Trips",
            "Match Rate (%)",
            "Veh-km Saved",
            "Veh-km Saved (%)",
            "Mean Driver Detour (m)",
            "P90 Driver Detour (m)",
            "Driver Gini",
            "Runtime (ms)",
        ]
        rows = []
        baseline_vkm = results["no_pool"].total_vkm_baseline_no_pool

        for key, res in results.items():
            pct_saved = (res.total_vkm_saved / baseline_vkm * 100.0) if baseline_vkm > 0 else 0.0
            rows.append([
                res.algorithm_name,
                str(len(res.matched_trips)),
                f"{res.match_rate_percent:.1f}%",
                f"{res.total_vkm_saved:.1f} km",
                f"{pct_saved:.1f}%",
                f"{res.mean_driver_detour_min:.1f}",
                f"{res.p90_driver_detour_min:.1f}",
                f"{res.gini_driver_detour:.4f}",
                f"{res.runtime_ms:.2f} ms",
            ])

        col_widths = [max(len(row[i]) for row in [headers] + rows) for i in range(len(headers))]
        header_line = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
        sep_line = "|-" + "-|-".join("-" * col_widths[i] for i in range(len(headers))) + "-|"
        row_lines = [
            "| " + " | ".join(r[i].ljust(col_widths[i]) for i, r in enumerate(headers)) + " |"
            for r in rows
        ]

        table_md = "\n".join([header_line, sep_line] + [
            "| " + " | ".join(row[i].ljust(col_widths[i]) for i in range(len(headers))) + " |"
            for row in rows
        ])
        return table_md
