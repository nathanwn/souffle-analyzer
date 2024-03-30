import pytest
from syrupy.assertion import SnapshotAssertion
from syrupy.extensions.single_file import SingleFileSnapshotExtension, WriteMode


class CustomFileSnapshotExtension(SingleFileSnapshotExtension):
    _write_mode = WriteMode.TEXT
    _file_extension = "snapshot"


@pytest.fixture
def file_snapshot(snapshot: SnapshotAssertion):
    return snapshot.with_defaults(extension_class=CustomFileSnapshotExtension)
