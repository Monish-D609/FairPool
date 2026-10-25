"""
FairPool Algorithms Module: Baselines, Shareability, Trip Enumeration, Solvers, and Fairness.
"""
from fairpool.algorithms.baselines import NoPoolingBaseline, GreedyNearestPairMatcher
from fairpool.algorithms.shareability import ShareabilityGraph
from fairpool.algorithms.enumeration import TripEnumerator
from fairpool.algorithms.fairness import FairnessEngine, compute_gini_coefficient
from fairpool.algorithms.solver import ExactILPSolver, GreedyApproximationSolver
from fairpool.algorithms.engine import FairPoolEngine

__all__ = [
    "NoPoolingBaseline",
    "GreedyNearestPairMatcher",
    "ShareabilityGraph",
    "TripEnumerator",
    "FairnessEngine",
    "compute_gini_coefficient",
    "ExactILPSolver",
    "GreedyApproximationSolver",
    "FairPoolEngine",
]
