from __future__ import annotations

import lsprotocol.types as lsp_types

from souffle_analyzer.ast import Position, Range


def get_lsp_types_from_method(method: str) -> tuple[type, ...] | None:
    return lsp_types.METHOD_TO_TYPES.get(method)


def get_request_type_from_method(method: str) -> type | None:
    types = get_lsp_types_from_method(method)
    if types is None:
        return None
    return types[0]


def get_response_type_from_method(method: str) -> type | None:
    types = get_lsp_types_from_method(method)
    if types is None:
        return None
    return types[1]


def to_lsp_position(position: Position) -> lsp_types.Position:
    return lsp_types.Position(line=position.line, character=position.char)


def from_lsp_position(position: lsp_types.Position) -> Position:
    return Position(
        line=position.line,
        char=position.character,
    )


def to_lsp_range(range_: Range) -> lsp_types.Range:
    return lsp_types.Range(
        start=to_lsp_position(range_.start),
        end=to_lsp_position(range_.end),
    )


def from_lsp_range(range_: lsp_types.Range) -> Range:
    return Range(
        start=from_lsp_position(range_.start),
        end=from_lsp_position(range_.end),
    )
