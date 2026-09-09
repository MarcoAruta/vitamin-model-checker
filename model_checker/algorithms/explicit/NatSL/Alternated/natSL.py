"""Space-oriented bounded NatSL model checking.

Strategy domains are generated lazily during depth-first quantifier evaluation.
"""

from model_checker.algorithms.explicit.NatSL.core import (
    model_checking as _model_checking,
)


def model_checking(formula, model):
    return _model_checking(formula, model, mode="space")
