import os

import pytest
from lsprotocol.types import Diagnostic
from syrupy.assertion import SnapshotAssertion

from souffle_analyzer.analysis import AnalysisContext
from souffle_analyzer.ast import Range
from souffle_analyzer.printer import format_souffle_code_range
from tests.util.helper import RangewiseResult, format_rangewise_results


@pytest.mark.parametrize(
    ("filename"),
    [
        ("semantic_arity1.dl"),
    ],
)
def test_diagnostic(file_snapshot: SnapshotAssertion, filename: str) -> None:
    test_data_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "testdata",
    )
    test_data_file = os.path.join(test_data_dir, filename)
    with open(test_data_file) as f:
        code = f.read()

    ctx = AnalysisContext()
    code_lines = code.splitlines()
    diagnostics = ctx.sync_document(test_data_file, code)
    rangewise_diagnostics = []

    for diagnostic in diagnostics:
        rangewise_diagnostics.append(
            RangewiseResult(
                cursor_range=Range.from_lsp_type(diagnostic.range), result=diagnostic
            )
        )

    def format_result(result: Diagnostic) -> list[str]:
        out = []
        out.append("-- Range --")
        out.extend(
            format_souffle_code_range(
                code_lines,
                filename,
                Range.from_lsp_type(result.range),
            )
        )
        out.append("-- Message --")
        out.append(result.message)
        return out

    assert (
        format_rangewise_results(
            code_lines=code_lines,
            uri=filename,
            format_result=format_result,
            rangewise_results=rangewise_diagnostics,
        )
        == file_snapshot
    )
