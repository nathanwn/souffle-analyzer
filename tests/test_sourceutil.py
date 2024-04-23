import inspect
from typing import Set

import pytest

from souffle_analyzer.sourceutil import (
    get_consecutive_block_at_line,
    get_words_in_consecutive_block_at_line,
)


@pytest.mark.parametrize(
    ("code", "line_no", "block"),
    [
        pytest.param(
            """
            foo

            path(source, sink) :- directed_edge(source, sink).
            path(source, sink) :- directed_edge(source, mid), path(mid, sink)

            bar
            """,
            2,
            """
            path(source, sink) :- directed_edge(source, sink).
            path(source, sink) :- directed_edge(source, mid), path(mid, sink)
            """,
            id="surrounded by blank lines",
        ),
        pytest.param(
            """
            // foo
            path(source, sink) :- directed_edge(source, sink).
            path(source, sink) :- directed_edge(source, mid), path(mid, sink)
            // bar
            """,
            1,
            """
            path(source, sink) :- directed_edge(source, sink).
            path(source, sink) :- directed_edge(source, mid), path(mid, sink)
            """,
            id="surrounded by line comments",
        ),
        pytest.param(
            """
            /* foo */
            path(source, sink) :- directed_edge(source, sink).
            path(source, sink) :- directed_edge(source, mid), path(mid, sink)
            /* bar */
            """,
            1,
            """
            path(source, sink) :- directed_edge(source, sink).
            path(source, sink) :- directed_edge(source, mid), path(mid, sink)
            """,
            id="surrounded by block comments",
        ),
    ],
)
def test_get_consecutive_block_at_line(
    code: str,
    line_no: int,
    block: str,
) -> None:
    code = inspect.cleandoc(code)
    block = inspect.cleandoc(block)
    assert get_consecutive_block_at_line(code, line_no) == block


@pytest.mark.parametrize(
    ("code", "line_no", "words"),
    [
        pytest.param(
            """
            foo

            path(source, sink) :- directed_edge(source, sink).
            path(source, sink) :- directed_edge(source, mid), path(mid, sink)

            bar
            """,
            2,
            {"path", "source", "sink", "directed_edge", "mid"},
            id="surrounded by blank lines",
        ),
        pytest.param(
            """
            // foo
            path(source, sink) :- directed_edge(source, sink).
            path(source, sink) :- directed_edge(source, mid), path(mid, sink)
            // bar
            """,
            1,
            {"path", "source", "sink", "directed_edge", "mid"},
            id="surrounded by line comments",
        ),
        pytest.param(
            """
            /* foo */
            path(source, sink) :- directed_edge(source, sink).
            path(source, sink) :- directed_edge(source, mid), path(mid, sink)
            /* bar */
            """,
            1,
            {"path", "source", "sink", "directed_edge", "mid"},
            id="surrounded by block comments",
        ),
    ],
)
def test_get_words_in_consecutive_block_at_line(
    code: str,
    line_no: int,
    words: Set[str],
) -> None:
    code = inspect.cleandoc(code)
    assert get_words_in_consecutive_block_at_line(code, line_no) == words
