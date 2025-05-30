from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from importlib import metadata as importlib_metadata

from souffle_analyzer.logging import configure_logging, get_default_log_location, logger
from souffle_analyzer.metadata import PROG
from souffle_analyzer.server import LanguageServer


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=PROG)
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {importlib_metadata.version(PROG)}",
        help=f"Get the version of {PROG}.",
    )

    subparsers = parser.add_subparsers(dest="command")

    server_parser = subparsers.add_parser("server", help="Run language server.")
    server_parser.add_argument(
        "--log-file",
        type=str,
        default=get_default_log_location(),
        help="Path to the log file. This creates a new file if it does not exist.",
    )
    server_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose mode.",
    )
    args = parser.parse_args(argv)

    if args.command == "server":
        configure_logging(args.log_file, args.verbose)
        logger.info(f"Started {PROG} in '{os.getcwd()}'.")
        server = LanguageServer(
            in_stream=sys.stdin.buffer,
            out_stream=sys.stdout.buffer,
        )
        server.serve()

    return 0
