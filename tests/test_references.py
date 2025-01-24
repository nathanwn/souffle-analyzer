import os
from typing import Optional

import lsprotocol.types as lsptypes
import pytest
from syrupy.assertion import SnapshotAssertion

from souffle_analyzer.analysis import AnalysisContext
from souffle_analyzer.ast import Position, Range
from souffle_analyzer.printer import format_souffle_code_range
from tests.util.helper import format_cursorwise_results


@pytest.mark.parametrize(
    ("filename"),
    [
        ("example1.dl"),
        ("example2.dl"),
        ("types2.dl"),
    ],
)
def test_references(file_snapshot: SnapshotAssertion, filename: str) -> None:
    test_data_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "testdata",
    )
    test_data_file = os.path.join(test_data_dir, filename)
    with open(test_data_file) as f:
        code = f.read()

    ctx = AnalysisContext()
    ctx.sync_document(filename, code)
    code_lines = code.splitlines()

    def analyze(position: Position) -> Optional[list[lsptypes.Location]]:
        result = ctx.get_references(filename, position.to_lsp_type())
        # Hide empty reference lists from test output
        if len(result) == 0:
            return None
        return result

    def format_result(result: list[lsptypes.Location]) -> list[str]:
        out = []
        out.append("-- References --")
        for loc in result:
            out.extend(
                format_souffle_code_range(
                    code_lines,
                    filename,
                    Range.from_lsp_type(loc.range),
                )
            )
            out.append("")
        return out

    assert (
        format_cursorwise_results(
            code_lines=code_lines,
            uri=filename,
            analyze=analyze,
            format_result=format_result,
        )
        == file_snapshot
    )
