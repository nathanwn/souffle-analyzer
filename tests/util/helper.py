import os
from dataclasses import dataclass
from typing import Any, Callable, Generic, List, Optional, TypeVar

from souffle_analyzer.ast import Position, Range
from souffle_analyzer.printer import format_souffle_code, format_souffle_code_range

T = TypeVar("T")


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
    code_lines: List[str],
    format_result: Callable[[Any], List[str]],
    rangewise_results: Any,
) -> str:
    out: List[str] = []

    for result in rangewise_results:
        assert result is not None
        out.append("-- Cursor range --")
        out.extend(format_souffle_code_range(code_lines, result.cursor_range))
        out.extend(format_result(result.result))
        out.extend(["_____", ""])

    return f"{os.linesep * 2}====={os.linesep * 2}".join(
        [
            os.linesep.join(format_souffle_code(code_lines)),
            os.linesep.join(out),
        ]
    )


def format_cursorwise_results(
    code_lines: List[str],
    analyze: Callable[[Position], Optional[Any]],
    format_result: Callable[[Any], List[str]],
) -> str:
    cur_start: Optional[Position] = None
    cur_end: Optional[Position] = None
    cur_result: Optional[object] = None

    rangewise_results: List[RangewiseResult] = []

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

    return format_rangewise_results(code_lines, format_result, rangewise_results)
