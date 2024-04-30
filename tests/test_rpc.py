import io
import json

import pytest
from hypothesis import given
from hypothesis import strategies as st

from souffle_analyzer.server import JsonRpcNode

arbitrary_json_msgs = st.recursive(
    st.none() | st.booleans() | st.text(),
    lambda children: st.lists(children) | st.dictionaries(st.text(), children),
    max_leaves=4,
)


@given(msg=arbitrary_json_msgs)
def test_read_one_valid_message(msg):
    content = json.dumps(msg)
    server = JsonRpcNode(
        in_stream=io.BytesIO(
            f"Content-Length: {len(content)}\r\n\r\n{content}".encode()
        ),
        out_stream=io.BytesIO(),
    )
    assert server.read_message() == msg


@given(msg=st.lists(arbitrary_json_msgs))
def test_read_valid_message_sequence(msg):
    content = json.dumps(msg)
    server = JsonRpcNode(
        in_stream=io.BytesIO(
            f"Content-Length: {len(content)}\r\n\r\n{content}".encode()
        ),
        out_stream=io.BytesIO(),
    )
    assert server.read_message() == msg


@given(sent_msg=arbitrary_json_msgs)
def test_json_rpc_roundtrip(sent_msg):
    # Simulating two JSON-RPC nodes communicating with each other.
    communication_stream = io.BytesIO()
    node1 = JsonRpcNode(
        in_stream=io.BytesIO(),
        out_stream=communication_stream,
    )
    node2 = JsonRpcNode(
        in_stream=communication_stream,
        out_stream=io.BytesIO(),
    )
    node1.write_message(sent_msg)
    # Reset the stream.
    communication_stream.seek(0)
    received_msg = node2.read_message()

    assert sent_msg == received_msg


@pytest.mark.parametrize(
    "raw_text",
    [
        pytest.param(
            "",
            id="Empty stream",
        ),
        pytest.param(
            "foo bar",
            id="Stream with invalid content",
        ),
        pytest.param(
            "Content-Length: foo\r\n\r\nbar",
            id="Invalid Content-Length",
        ),
        pytest.param(
            "Content-Length: 42\r\nfoo\r\nbar",
            id="Invalid separator",
        ),
    ],
)
def test_read_invalid_message(raw_text: str):
    server = JsonRpcNode(
        in_stream=io.BytesIO(raw_text.encode()),
        out_stream=io.BytesIO(),
    )
    assert server.read_message() is None
