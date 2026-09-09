"""Time-oriented bounded NatSL model checking.

Strategy domains are materialized once; failed existentially-pruned models are
retained for the bounded universal phase.
"""

from model_checker.algorithms.explicit.NatSL.core import (
    model_checking as _model_checking,
)


def model_checking(formula, model):
    return _model_checking(formula, model, mode="time")
