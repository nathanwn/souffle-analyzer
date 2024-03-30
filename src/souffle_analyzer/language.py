from typing import NamedTuple


class BuiltinType(NamedTuple):
    name: str
    doc: str


BUILTIN_TYPES = [
    BuiltinType(
        name="symbol",
        doc="Type `symbol`. Each value is a string.",
    ),
    BuiltinType(
        name="number",
        doc="Type `number`. Each value is a signed integer.",
    ),
    BuiltinType(
        name="unsigned",
        doc="Type `unsigned`. Each value is a non-negative integer.",
    ),
    BuiltinType(
        name="float",
        doc="Type `float`. Each value is a floating-point number.",
    ),
]
