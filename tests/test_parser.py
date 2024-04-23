import os

import pytest
from syrupy.assertion import SnapshotAssertion

from souffle_analyzer.parser import Parser
from souffle_analyzer.printer import (
    format_souffle_ast,
    format_souffle_code,
    get_positions_in_range,
)


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
        ("syntax_incomplete1.dl"),
    ],
)
def test_parser(file_snapshot: SnapshotAssertion, filename: str) -> None:
    test_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testdata")
    test_data_file = os.path.join(test_data_dir, filename)
    with open(test_data_file, "rb") as f:
        code = f.read()
    parser = Parser()
    file = parser.parse(code)

    res = os.linesep.join(format_souffle_ast(file))
    assert res.replace(os.linesep, "\n") == file_snapshot


@pytest.mark.parametrize(
    ("filename"),
    [
        ("example1.dl"),
        ("syntax_error_1.dl"),
        ("subsumption1.dl"),
        ("types1.dl"),
        ("types3.dl"),
        ("include_preproc_directive.dl"),
        ("syntax_incomplete1.dl"),
    ],
)
def test_parser_on_incomplete_files(
    filename: str,
) -> None:
    test_data_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "testdata",
    )
    test_data_file = os.path.join(test_data_dir, filename)
    with open(test_data_file, "rb") as f:
        code = f.read()

    parser = Parser()
    file = parser.parse(code)
    code_lines = code.decode().splitlines()

    all_positions = get_positions_in_range(
        range_=file.range_,
        code_lines=code_lines,
    )

    for i in range(len(all_positions)):
        prev = None
        new_code_buf = []
        for j in range(i + 1, len(all_positions)):
            cur = all_positions[j]
            if prev is not None and prev.line != cur.line:
                new_code_buf.append(os.linesep)
            new_code_buf.append(code_lines[cur.line][cur.character])
            prev = cur
            new_code = "".join(new_code_buf).encode()
            try:
                parser.parse(new_code)
            except BaseException as err:
                pytest.fail(
                    os.linesep.join(
                        [
                            str(f"Unexpected error: {err}"),
                            *format_souffle_code(new_code.decode().splitlines()),
                        ],
                    )
                )
