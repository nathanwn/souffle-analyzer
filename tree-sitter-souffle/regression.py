#!/usr/bin/env python3

import os
import subprocess
from glob import glob
from typing import NamedTuple


class TestRepo(NamedTuple):
    url: str
    name: str
    version: str
    skipped_cases: list[str]
    ignored_cases: list[str]


TEST_REPOS_DIR = "build/testrepos"
TEST_DATA = [
    TestRepo(
        name="souffle",
        url="https://github.com/souffle-lang/souffle",
        version="2.5",
        skipped_cases=[
            # Undocumented features
            # - https://github.com/souffle-lang/souffle-lang.github.io/issues/136
            "tests/semantic/iteration_counter/iteration_counter.dl",
            # - Lattice: https://github.com/souffle-lang/souffle/pull/2438
            "tests/interface/lattice3/lattice3.dl",
            "tests/interface/lattice2/lattice2.dl",
            "tests/interface/lattice1/lattice1.dl",
            # - IP addresses: https://github.com/souffle-lang/souffle/pull/180
            "tests/semantic/ipv4_1/ipv4_1.dl",
            "tests/semantic/ipv4/ipv4.dl",
            # C-style macros
            "tests/semantic/string_minmax/string_minmax.dl",
            "tests/semantic/comparison/comparison.dl",
            # Needs investigation
            "tests/semantic/type_system16/type_system16.dl",
            "tests/interface/aggregates/aggregates.dl",
        ],
        ignored_cases=[
            # Intentional syntax errors and should be ignored (?)
            "tests/syntactic/sourceloc5/sourceloc5.dl",
            "tests/syntactic/syntax2/syntax2.dl",
            "tests/syntactic/sourceloc2/sourceloc2.dl",
            "tests/syntactic/syntax3/syntax3.dl",
            "tests/syntactic/syntax5/syntax5.dl",
            "tests/syntactic/syntax9/syntax9.dl",
            "tests/syntactic/syntax8/syntax8.dl",
            "tests/syntactic/syntax10/syntax10.dl",
            "tests/syntactic/syntax7/syntax7.dl",
            "tests/syntactic/syntax1/syntax1.dl",
            "tests/syntactic/sourceloc4/sourceloc4.dl",
            "tests/syntactic/sourceloc1/sourceloc1.dl",
            "tests/syntactic/include_directive3/include_directive3.dl",
            "tests/syntactic/annotations/annotations.dl",
            "tests/syntactic/issue2408/issue2408.dl",
            "tests/syntactic/doc_comment_dangling3/doc_comment_dangling3.dl",
            "tests/syntactic/include_directive4/q2/q2.dl",
            "tests/syntactic/include_directive4/q1/q1.dl",
            "tests/syntactic/syntax4/syntax4.dl",
            "tests/syntactic/sourceloc3/sourceloc3.dl",
            "tests/syntactic/rule/rule.dl",
            "tests/syntactic/syntax6/syntax6.dl",
            "tests/syntactic/qualifiers4/qualifiers4.dl",
            "tests/syntactic/unterminated_comment/unterminated_comment.dl",
            "tests/syntactic/cpp_keywords/cpp_keywords.dl",
            "tests/syntactic/execution_plan/execution_plan.dl",
        ],
    ),
]


def clone_repo(test_repo: TestRepo) -> None:
    subprocess.run(
        args=[
            *("git", "clone", "--filter=blob:none"),
            *(test_repo.url, test_repo.name),
        ],
        cwd=TEST_REPOS_DIR,
    )
    subprocess.run(
        args=["git", "checkout", test_repo.version],
        cwd=os.path.join(TEST_REPOS_DIR, test_repo.name),
    )


def main() -> int:
    subprocess.run(args=["pwd"])
    if not os.path.isdir(TEST_REPOS_DIR):
        os.makedirs(TEST_REPOS_DIR, exist_ok=True)
    for test_repo in TEST_DATA:
        if not os.path.isdir(os.path.join(TEST_REPOS_DIR, test_repo.name)):
            clone_repo(test_repo)

    total_cnt_failed = 0

    for test_repo in TEST_DATA:
        cnt_failed = 0
        cnt_ignored = 0
        cnt_passed = 0
        cnt_skipped = 0

        ignored_tests = set(
            map(
                lambda case: os.path.join(TEST_REPOS_DIR, test_repo.name, case),
                test_repo.ignored_cases,
            )
        )

        skipped_tests = set(
            map(
                lambda case: os.path.join(TEST_REPOS_DIR, test_repo.name, case),
                test_repo.skipped_cases,
            )
        )

        for filepath in glob("**/*.dl", recursive=True):
            print(filepath, end=": ", flush=True)
            if filepath in ignored_tests:
                print("IGNORED")
                cnt_ignored += 1
                continue
            if filepath in skipped_tests:
                print("SKIPPED")
                cnt_skipped += 1
                continue

            res = subprocess.run(
                args=[
                    *("npx", "tree-sitter", "parse", "--quiet"),
                    filepath,
                ],
                check=False,
                capture_output=True,
            )
            if res.returncode != 0:
                print("FAILED")
                err_log = res.stdout.decode().replace(filepath, "").strip()
                print(err_log)
                cnt_failed += 1
            else:
                print("PASSED")
                cnt_passed += 1

        total = cnt_passed + cnt_failed + cnt_skipped
        passed_percentage = 100.0 * cnt_passed / total
        print(
            " ".join(
                [
                    "Result: ",
                    "; ".join(
                        [
                            f"passed[{cnt_passed}/{total} ({passed_percentage:.2f}%)]",
                            f"failed[{cnt_failed}/{total}]",
                            f"skipped[{cnt_skipped}/{total}]",
                        ]
                    ),
                ]
            )
        )

        total_cnt_failed += cnt_failed

    return int(bool(total_cnt_failed))


if __name__ == "__main__":
    raise SystemExit(main())
