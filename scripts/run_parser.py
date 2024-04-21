import argparse

from souffle_analyzer.parser import Parser
from souffle_analyzer.printer import format_souffle_ast


def main() -> int:
    arg_parser = argparse.ArgumentParser()
    subparsers = arg_parser.add_subparsers()
    parse_parser = subparsers.add_parser("parse")
    parse_parser.add_argument("filename", type=str)
    args = arg_parser.parse_args()
    if args.filename:
        with open(args.filename, "rb") as f:
            content = f.read()
        souffle_parser = Parser()
        ast = souffle_parser.parse(content)
        print("\n".join(format_souffle_ast(ast)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
