import pytest

from souffle_analyzer.ast import BlockComment, LineComment, Location, Position, Range


@pytest.mark.parametrize(
    ("content", "text"),
    [
        pytest.param(
            """
         /**
          * This is the first line
          * This is the second line
         **/
         """,
            ["This is the first line", "This is the second line"],
            id="Normal block comment",
        ),
        pytest.param(
            """
            /**
            **/
            """,
            [],
            id="Empty comment 1",
        ),
        pytest.param(
            """
            /**
            **/
            """,
            [],
            id="Empty comment 2",
        ),
    ],
)
def test_block_comment_get_text(content: str, text: str):
    block_comment = BlockComment(
        location=Location(
            uri="",
            range_=Range(Position(0, 0), Position(1, 1)),
        ),
        content=content,
    )
    assert block_comment.get_text() == text


@pytest.mark.parametrize(
    ("content", "text"),
    [
        pytest.param(
            """
            //
            // This is the first line
            // This is the second line
            //
            """,
            ["This is the first line", "This is the second line"],
            id="Comment with leading and trailing blank lines",
        ),
        pytest.param(
            """
            //
            """,
            [],
            id="Empty comment",
        ),
    ],
)
def test_line_comment_get_text(content: str, text: str):
    line_comment = LineComment(
        location=Location(
            uri="",
            range_=Range(Position(0, 0), Position(1, 1)),
        ),
        content=content.splitlines(),
    )
    assert line_comment.get_text() == text
