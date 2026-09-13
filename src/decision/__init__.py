"""Package `decision`: agricultural decision-support layer.

Deterministic, explainable and versioned. The decision engine is the authority;
a language model may only rephrase its output (see serving.groq_explain). All
threshold knobs live in data/decision/ and are never hard-coded in the UI.
"""
from src.decision.engine import (Decision, DecisionError, build_decision,
                                 decision_from_serving)
from src.decision.signals import false_onset_risk, monsoon_status

__all__ = [
    "Decision",
    "DecisionError",
    "build_decision",
    "decision_from_serving",
    "false_onset_risk",
    "monsoon_status",
]