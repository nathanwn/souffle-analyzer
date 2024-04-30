import json
from typing import BinaryIO, Optional

from souffle_analyzer.logging import logger


class JsonRpcNode:
    def __init__(self, in_stream: BinaryIO, out_stream: BinaryIO) -> None:
        self.in_stream = in_stream
        self.out_stream = out_stream

    def read_message(self) -> Optional[dict]:
        content_length_prefix = b"Content-Length:"
        content_length = None
        content_length_prefix_pos = -1

        while True:
            # Read until we find the Content-Length header or EOF.
            line = self.in_stream.readline()
            if not line:  # EOF
                return None
            content_length_prefix_pos = line.find(content_length_prefix)
            if content_length_prefix_pos == -1:
                continue

            try:
                content_length = int(
                    line[
                        content_length_prefix_pos + len(content_length_prefix) :
                    ].strip()
                )
            except ValueError:
                logger.warning("Content-Length value in header is not a valid integer.")
                return None

            if len(self.in_stream.readline().strip()) != 0:  # second '\r\n'
                logger.warning("Second \\r\\n not found while reading message.")
                return None

            body = self.in_stream.read(content_length)
            break

        # Read the message from the body
        try:
            message = json.loads(body)
        except json.JSONDecodeError as e:
            logger.error("Error while decoding message: %s", e)
            logger.error("body is: %s", body)
            logger.error("content length is: %s", content_length)
            return None

        return message

    def write_message(self, message: object) -> None:
        logger.info("Replying with message: %s.", message)
        encoded_msg = self.encode_message(message)
        self.out_stream.write(encoded_msg)
        self.out_stream.flush()

    def encode_message(self, message: object) -> bytes:
        content = json.dumps(message)
        message = f"Content-Length: {len(content)}\r\n\r\n{content}".encode()
        return message
