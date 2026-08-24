from .parser import (
    AtomicProp,
    Binary,
    BooleanConst,
    ClockExpr,
    DemonicBinary,
    DemonicOp,
    Expr,
    FreezeExpr,
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
    "DemonicBinary",
    "DemonicOp",
    "Expr",
    "FreezeExpr",
    "SimpleTimeExpr",
    "Unary",
]
