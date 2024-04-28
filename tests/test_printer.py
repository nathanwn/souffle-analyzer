import os

import pytest
from syrupy.assertion import SnapshotAssertion

from souffle_analyzer.printer import format_souffle_code


@pytest.mark.parametrize(
    ("filename"),
    [
        ("example1.dl"),
        ("syntax_error_1.dl"),
        ("subsumption1.dl"),
        ("types1.dl"),
    ],
)
def test_printer(file_snapshot: SnapshotAssertion, filename: str) -> None:
    test_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testdata")
    test_data_file = os.path.join(test_data_dir, filename)
    with open(test_data_file) as f:
        code = f.read()
    res = os.linesep.join(format_souffle_code(code.splitlines(), uri=filename))
    assert res.replace(os.linesep, "\n") == file_snapshot
