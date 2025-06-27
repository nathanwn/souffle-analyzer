import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from souffle_analyzer.ast import Position, Range
from souffle_analyzer.printer import format_souffle_code, format_souffle_code_range

T = TypeVar("T")


def parse_code_with_cursor_position(code_with_cursor: str) -> tuple[str, Position]:
    code_with_cursor = clean_multiline_string(code_with_cursor)
    lines = code_with_cursor.splitlines()
    cursor_line = -1
    for i, line in enumerate(lines):
        if line.strip() == "^":
            cursor_line = i
            break
    assert cursor_line != -1
    code_lines = []
    for i, line in enumerate(lines):
        if i == cursor_line:
            continue
        code_lines.append(line)
    cursor_pos = Position(line=cursor_line - 1, character=lines[cursor_line].find("^"))
    return os.linesep.join(code_lines), cursor_pos


def clean_multiline_string(s: str):
    def is_empty_line(line: str):
        return len(line.strip()) == 0

    lines = s.splitlines()
    start_line = 0
    while start_line < len(lines) and is_empty_line(lines[start_line]):
        start_line += 1
    end_line = len(lines) - 1
    while end_line > -1 and is_empty_line(lines[end_line]):
        end_line -= 1
    min_leading_whitespaces = int(1e9)
    for line_no in range(start_line, end_line + 1):
        line = lines[line_no]
        if is_empty_line(line):
            continue
        i = 0
        while i < len(line) and line[i] == " ":
            i += 1
        min_leading_whitespaces = min(min_leading_whitespaces, i)
    new_lines = []
    for line_no in range(start_line, end_line + 1):
        line = lines[line_no]
        new_lines.append(line[min_leading_whitespaces:])
    return os.linesep.join(new_lines)


@dataclass
class RangewiseResult(Generic[T]):
    cursor_range: Range
    result: T


def format_rangewise_results(
    code_lines: list[str],
    uri: str,
    format_result: Callable[[Any], list[str]],
    rangewise_results: Any,
) -> str:
    out: list[str] = []

    for result in rangewise_results:
        assert result is not None
        out.append("-- Cursor range --")
        out.extend(format_souffle_code_range(code_lines, uri, result.cursor_range))
        out.extend(format_result(result.result))
        out.extend(["_____", ""])

    return "\n\n=====\n\n".join(
        [
            "\n".join(format_souffle_code(code_lines, uri=uri)),
            "\n".join(out),
        ]
    )


def format_cursorwise_results(
    code_lines: list[str],
    uri: str,
    analyze: Callable[[Position], Any | None],
    format_result: Callable[[Any], list[str]],
) -> str:
    cur_start: Position | None = None
    cur_end: Position | None = None
    cur_result: object | None = None

    rangewise_results: list[RangewiseResult] = []

    for line_no, line in enumerate(code_lines):
        for char_no, _ in enumerate(line):
            pos = Position(line_no, char_no)
            result = analyze(pos)
            if result != cur_result:
                if cur_result is not None:
                    assert cur_start is not None
                    assert cur_end is not None
                    rangewise_results.append(
                        RangewiseResult(
                            Range(start=cur_start, end=cur_end),
                            cur_result,
                        )
                    )

                if result is None:
                    cur_result = None
                    cur_start = None
                    cur_end = None
                else:
                    cur_result = result
                    cur_start = pos
                    # Range-end char index must be exclusive
                    cur_end = Position(line=pos.line, character=pos.character + 1)
            else:
                if cur_end is not None:
                    # Range-end char index must be exclusive
                    cur_end = Position(line=pos.line, character=pos.character + 1)

    if cur_start is not None and cur_end is not None and cur_result is not None:
        rangewise_results.append(
            RangewiseResult(
                Range(start=cur_start, end=cur_end),
                cur_result,
            )
        )

    return format_rangewise_results(code_lines, uri, format_result, rangewise_results)
