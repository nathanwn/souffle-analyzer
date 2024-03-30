from typing import Any, Callable, List, NamedTuple, Optional

from souffle_analyzer.ast import Position, Range
from souffle_analyzer.printer import format_souffle_code, format_souffle_code_range


class ResultAtCursor(NamedTuple):
    cursor_range: Range
    result: Any


def record_analysis_result_at_cursor(
    code_lines: List[str],
    analyze: Callable[[Position], Optional[Any]],
    format_result: Callable[[Any], List[str]],
) -> str:
    cur_start: Optional[Position] = None
    cur_end: Optional[Position] = None
    cur_result: Optional[object] = None

    results: List[ResultAtCursor] = []

    for line_no, line in enumerate(code_lines):
        for char_no, _ in enumerate(line):
            pos = Position(line_no, char_no)
            result = analyze(pos)
            if result != cur_result:
                if cur_result is not None:
                    assert cur_start is not None
                    assert cur_end is not None
                    results.append(
                        ResultAtCursor(
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
                    cur_end = pos
            else:
                if cur_end is not None:
                    cur_end = pos

    if cur_start is not None and cur_end is not None and cur_result is not None:
        results.append(
            ResultAtCursor(
                Range(start=cur_start, end=cur_end),
                cur_result,
            )
        )

    out: List[str] = []

    for result in results:
        assert result is not None
        out.append("-- Cursor range --")
        out.extend(format_souffle_code_range(code_lines, result.cursor_range))
        out.extend(format_result(result.result))
        out.extend(["_____", ""])

    return "\n\n=====\n\n".join(
        [
            "\n".join(format_souffle_code(code_lines)),
            "\n".join(out),
        ]
    )
