from typing import List

from souffle_analyzer.ast import Argument, Node, Position, Range


def get_positions_in_range(range_: Range, code_lines: List[str]) -> List[Position]:
    start = range_.start
    end = range_.end
    cur = Position(start.line, start.character)
    res = []

    while cur < end:
        res.append(cur)
        if cur.character + 1 >= len(code_lines[cur.line]):
            cur = Position(cur.line + 1, 0)
            # Skip empty lines
            while cur.line < len(code_lines) and len(code_lines[cur.line]) == 0:
                cur = Position(cur.line + 1, 0)
        else:
            cur = Position(cur.line, cur.character + 1)

    return res


def format_souffle_code(lines: List[str], uri: str) -> List[str]:
    printed_lines = [uri]
    max_line_no = len(lines) - 1
    for line_no, line in enumerate(lines):
        sidebar = str(line_no).rjust(len(str(max_line_no)))
        if len(line.strip()) == 0:
            printed_lines.append(f"{sidebar} |")
        else:
            printed_lines.append(f"{sidebar} | {line}")
    return printed_lines


def format_souffle_code_range(lines: List[str], uri: str, range_: Range) -> List[str]:
    max_line_no = len(lines) - 1
    sidebar_size = len(str(max_line_no))
    printed_lines = [uri]

    for line_no in range(range_.start.line, range_.end.line + 1):
        marker_line_chars = [" " for _ in range(len(lines[line_no]))]
        for char_no in range(len(lines[line_no])):
            if range_.covers(Position(line_no, char_no)):
                marker_line_chars[char_no] = "~"
        # Special case: if range start and range end are the same, intepret it
        # as a single position.
        if range_.start == range_.end:
            marker_line_chars[range_.start.character] = "^"
        marker_line = "".join(marker_line_chars).rstrip()
        code_line = lines[line_no].rstrip()
        printed_lines.append(f"{str(line_no).rjust(sidebar_size)} | {code_line}")
        printed_lines.append(f"{''.rjust(sidebar_size)} | {marker_line}")

    return printed_lines


def indent(s: str, level: int) -> str:
    size = 2
    return f"{(level * size) * ' '}{s}"


def format_souffle_ast(node: Node, level=0) -> List[str]:
    children = node.children_sorted_by_range
    if len(children) == 0:
        return [indent(str(node), level=level)]
    else:
        res = []
        res.append(indent(f"{type(node).__name__}(", level=level))
        res.append(indent(f"range_={node.range_}", level=level + 1))
        if isinstance(node, Argument):
            res.append(indent(f"ty={node.ty}", level=level + 1))

        for child in children:
            res.extend(format_souffle_ast(node=child, level=level + 1))

        # if node.syntax_issues:
        #     res.append(indent("SyntaxIssues[", level + 1))
        #     for issue in node.syntax_issues:
        #         res.append(indent(str(issue), level + 2) + ",")
        #     res.append(indent("]", level + 1))

        res.append(indent(")", level=level))
        return res
