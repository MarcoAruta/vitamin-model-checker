from .parser import (
    AtomicProp,
    Binary,
    BooleanConst,
    ClockExpr,
    Expr,
    FreezeExpr,
    QuantifiedPath,
    SimpleTimeExpr,
    Unary,
)

METADATA = {"model_type": "timedCGS"}

__all__ = [
    "METADATA",
    "AtomicProp",
    "Binary",
    "BooleanConst",
    "ClockExpr",
    "Expr",
    "FreezeExpr",
    "QuantifiedPath",
    "SimpleTimeExpr",
    "Unary",
]
