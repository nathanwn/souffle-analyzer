import os
from typing import List, Optional

import pytest
from lsprotocol import types as lsptypes
from syrupy.assertion import SnapshotAssertion

from souffle_analyzer.analysis import AnalysisContext
from souffle_analyzer.ast import Position
from souffle_analyzer.lsp import from_lsp_range, to_lsp_position
from souffle_analyzer.printer import format_souffle_code_range
from tests.util.helper import record_analysis_result_at_cursor


@pytest.mark.parametrize(
    ("filename"),
    [
        ("example1.dl"),
        ("example3.dl"),
    ],
)
def test_hover(file_snapshot: SnapshotAssertion, filename: str) -> None:
    test_data_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "testdata",
    )
    test_data_file = os.path.join(test_data_dir, filename)
    with open(test_data_file) as f:
        code = f.read()

    ctx = AnalysisContext()
    ctx.open_document(filename, code)
    code_lines = code.splitlines()

    def analyze(position: Position) -> Optional[List[lsptypes.TextEdit]]:
        return ctx.get_code_actions(filename, to_lsp_position(position))

    def format_result(result: List[lsptypes.TextEdit]) -> List[str]:
        out = []
        out.append("-- Insertion point --")
        out.extend(
            format_souffle_code_range(code_lines, from_lsp_range(result[0].range))
        )
        out.append("--  Text  --")
        out.extend(result[0].new_text.splitlines())
        return out

    assert (
        record_analysis_result_at_cursor(
            code_lines=code_lines,
            analyze=analyze,
            format_result=format_result,
        )
        == file_snapshot
    )
