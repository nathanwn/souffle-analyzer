from typing import Set

import pytest
from lsprotocol.types import CompletionContext, CompletionTriggerKind

from souffle_analyzer.analysis import AnalysisContext
from tests.util.helper import parse_code_with_cursor_position


@pytest.mark.parametrize(
    ("code_with_cursor_position", "completion_label_set"),
    [
        pytest.param(
            """
            .decl foo(x: number)

            f
             ^
            """,
            {"foo"},
            id="fact name completion 1",
        ),
        pytest.param(
            """
            .decl foo(x: number)
            .decl bar(x: number)
            .decl baz(x: number)

            b
             ^
            """,
            {"bar", "baz"},
            id="fact name completion 2",
        ),
        pytest.param(
            """
            .decl directed_edge(initial: number, terminal: number)

            .decl path(source: number, sink: number)

            path(source, sink) :- directed_edge(source, sink).
            path(source, sink) :- directed_edge(source, mid), path(m
                                                                    ^
            """,
            {"mid"},
            id="argument name completion 1",
        ),
        pytest.param(
            """
            .decl directed_edge(initial: number, terminal: number)

            .decl path(source: number, sink: number)

            path(source, sink) :- directed_edge(source, sink).
            path(source, sink) :- directed_edge(s
                                                 ^
            """,
            {"source", "sink"},
            id="argument name completion 2",
        ),
        pytest.param(
            """
            .decl directed_edge(initial: number, terminal: n
                                                            ^
            """,
            {"number"},
            id="built-in type name completion",
        ),
        pytest.param(
            """
            .type negative_number <: number

            .decl greater_than(x: number, y: n
                                              ^
            """,
            {"number", "negative_number"},
            id="user-defined type name completion",
        ),
    ],
)
def test_completion_no_trigger_character(
    code_with_cursor_position: str, completion_label_set: Set[str]
) -> None:
    code, cursor_position = parse_code_with_cursor_position(code_with_cursor_position)
    ctx = AnalysisContext()
    uri = "main.dl"
    ctx.sync_document(uri=uri, text=code)
    completion_items = ctx.get_completion_items(
        uri=uri,
        position=cursor_position.to_lsp_type(),
        context=CompletionContext(
            trigger_kind=CompletionTriggerKind.Invoked,
            trigger_character=None,
        ),
    )
    completion_labels = [_.label for _ in completion_items]
    assert completion_label_set.issubset(completion_labels)


def test_completion_with_trigger_character() -> None:
    code, cursor_position = parse_code_with_cursor_position(
        """
        .
         ^
        """,
    )
    ctx = AnalysisContext()
    uri = "main.dl"
    ctx.sync_document(uri=uri, text=code)
    completion_items = ctx.get_completion_items(
        uri=uri,
        position=cursor_position.to_lsp_type(),
        context=CompletionContext(
            trigger_kind=CompletionTriggerKind.Invoked,
            trigger_character=".",
        ),
    )
    completion_labels = [_.label for _ in completion_items]
    assert {"decl", "input", "output", "type"}.issubset(completion_labels)
