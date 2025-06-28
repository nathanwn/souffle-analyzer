import os

import pytest

from souffle_analyzer.printer import format_souffle_code
from tests.util.helper import write_output_file


@pytest.mark.parametrize(
    ("filename"),
    [
        ("example1.dl"),
        ("syntax_error_1.dl"),
        ("subsumption1.dl"),
        ("types1.dl"),
    ],
)
def test_printer(
    update_output: bool,
    test_data_dir: str,
    filename: str,
) -> None:
    test_data_file = os.path.join(test_data_dir, filename)
    with open(test_data_file) as f:
        code = f.read()
    result = os.linesep.join(format_souffle_code(code.splitlines(), uri=filename))
    result = result.replace(os.linesep, "\n")

    out_file = os.path.join(test_data_dir, "test_printer", filename + ".out")
    if update_output:
        write_output_file(out_file, result)
    else:
        with open(out_file) as f:
            output = f.read()
        assert result == output
