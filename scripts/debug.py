import argparse
import os
from typing import List, Optional

import lsprotocol.types as lsptypes

from souffle_analyzer.analysis import AnalysisContext
from souffle_analyzer.ast import Position, Range
from souffle_analyzer.parser import Parser
from souffle_analyzer.printer import (
    format_souffle_ast,
    format_souffle_code,
    format_souffle_code_range,
)


def analyze(
    ctx: AnalysisContext,
    filename: str,
    position: Position,
) -> Optional[List[lsptypes.Location]]:
    result = ctx.get_references(filename, position.to_lsp_type())
    # Hide empty reference lists from test output
    if len(result) == 0:
        return None
    return result


def format_result(
    code_lines: List[str],
    result: List[lsptypes.Location],
) -> List[str]:
    out = []
    out.append("-- References --")
    for loc in result:
        out.extend(
            format_souffle_code_range(
                code_lines,
                Range.from_lsp_type(loc.range),
            )
        )
        out.append("")
    return out


def main() -> int:
    arg_parser = argparse.ArgumentParser()
    subparsers = arg_parser.add_subparsers(dest="command")

    parse_parser = subparsers.add_parser(name="parse")
    parse_parser.add_argument("filename", type=str)

    references_parser = subparsers.add_parser("references")
    references_parser.add_argument(
        "filename",
        type=str,
    )
    references_parser.add_argument(
        *("-l", "--line"),
        type=int,
    )
    references_parser.add_argument(
        *("-c", "--character"),
        type=int,
    )

    args = arg_parser.parse_args()

    if args.command == "parse":
        with open(args.filename) as f:
            content = f.read()
        souffle_parser = Parser()
        ast = souffle_parser.parse(content.encode())
        print(os.linesep.join(format_souffle_ast(ast)))
    elif args.command == "references":
        ctx = AnalysisContext()
        with open(args.filename) as f:
            content = f.read()
        code_lines = content.splitlines()
        ctx.open_document(args.filename, content)
        result = analyze(
            ctx,
            args.filename,
            position=Position(line=args.line, character=args.character),
        )
        print("-- File --")
        print(os.linesep.join(format_souffle_code(code_lines)))
        print("-- Cursor --")
        print(
            os.linesep.join(
                format_souffle_code_range(
                    code_lines,
                    range_=Range.from_single_position(
                        Position(args.line, args.character)
                    ),
                )
            )
        )
        if result is None:
            print("Result is None")
        else:
            print(os.linesep.join(format_result(content.splitlines(), result)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
