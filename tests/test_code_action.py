import os

import pytest
from lsprotocol import types as lsptypes

from souffle_analyzer.analysis import AnalysisContext
from souffle_analyzer.ast import Position, Range
from souffle_analyzer.printer import format_souffle_code_range
from tests.util.helper import format_by_position_results, write_output_file


@pytest.mark.parametrize(
    ("filename"),
    [
        ("example1.dl"),
        ("example3.dl"),
    ],
)
def test_hover(
    update_output: bool,
    test_data_dir: str,
    filename: str,
) -> None:
    test_data_file = os.path.join(test_data_dir, filename)
    with open(test_data_file) as f:
        code = f.read()

    ctx = AnalysisContext()
    ctx.sync_document(filename, code)
    code_lines = code.splitlines()

    def analyze(position: Position) -> list[lsptypes.TextEdit] | None:
        return ctx.get_code_actions(filename, position.to_lsp_type())

    def format_result(result: list[lsptypes.TextEdit]) -> list[str]:
        out = []
        out.append("-- Insertion point --")
        out.extend(
            format_souffle_code_range(
                code_lines,
                uri=filename,
                range_=Range.from_lsp_type(result[0].range),
            )
        )
        out.append("--  Text  --")
        out.extend(result[0].new_text.splitlines())
        return out

    result = format_by_position_results(
        code_lines=code_lines,
        uri=filename,
        analyze=analyze,
        format_result=format_result,
    )

    out_file = os.path.join(test_data_dir, "test_code_action", filename + ".out")
    if update_output:
        write_output_file(out_file, result)
    else:
        with open(out_file) as f:
            output = f.read()
        assert result == output
