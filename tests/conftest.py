import os

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--update-output",
        action="store_true",
        help="Update expected output of tests",
    )


@pytest.fixture
def update_output(request) -> bool:
    return request.config.getoption("--update-output")


def get_test_root_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def test_root_dir() -> str:
    return get_test_root_dir()


@pytest.fixture
def test_data_dir() -> str:
    return os.path.join(get_test_root_dir(), "testdata")
