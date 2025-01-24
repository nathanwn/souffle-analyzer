import pytest

from souffle_analyzer.sourceutil import (
    get_consecutive_block_at_line,
    get_words_in_consecutive_block_at_line,
)
from tests.util.helper import clean_multiline_string


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
    code = clean_multiline_string(code)
    block = clean_multiline_string(block)
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
    words: set[str],
) -> None:
    code = clean_multiline_string(code)
    assert get_words_in_consecutive_block_at_line(code, line_no) == words
