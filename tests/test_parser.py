import os

import pytest
from syrupy.assertion import SnapshotAssertion

from souffle_analyzer.parser import Parser
from souffle_analyzer.printer import format_souffle_ast


@pytest.mark.parametrize(
    ("filename"),
    [
        ("example1.dl"),
        ("example2.dl"),
        ("syntax_error_1.dl"),
        ("subsumption1.dl"),
        ("types1.dl"),
        ("types2.dl"),
        ("types3.dl"),
        ("include_preproc_directive.dl"),
    ],
)
def test_parser(file_snapshot: SnapshotAssertion, filename: str) -> None:
    test_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testdata")
    test_data_file = os.path.join(test_data_dir, filename)
    with open(test_data_file, "rb") as f:
        code = f.read()
    parser = Parser()
    program = parser.parse(code)

    res = "\n".join(format_souffle_ast(program))
    print(file_snapshot.test_location)
    assert res == file_snapshot
