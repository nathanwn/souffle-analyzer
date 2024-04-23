import re
from typing import List, Set


def get_consecutive_block_at_line(
    code: str,
    line_no: int,
) -> str:
    code_lines = code.splitlines()
    start = line_no
    while start - 1 > -1 and len(code_lines[start - 1]) > 0:
        stripped_code_line = code_lines[start - 1].strip()
        if stripped_code_line.startswith("//") or stripped_code_line.endswith("*/"):
            break
        start -= 1
    end = line_no
    while end + 1 < len(code_lines) and len(code_lines[end + 1]) > 0:
        stripped_code_line = code_lines[end + 1].strip()
        if stripped_code_line.startswith("//") or stripped_code_line.startswith("/*"):
            break
        end += 1
    lines = []
    for line_no in range(start, end + 1):
        lines.append(code_lines[line_no])
    return "\n".join(lines)


def get_words_in_consecutive_block_at_line(code: str, line_no: int) -> Set[str]:
    block = get_consecutive_block_at_line(code, line_no)
    words = re.split(r"[^\w]+", block)
    res = set(filter(lambda _: len(_) > 0, words))
    return res


def get_bracket_scores(code: str) -> List[List[int]]:
    # On each line, there is always at least a value marking the
    # bracket score at the "beginning" of the line before
    # any character appears.
    # This property helps dealing with empty lines.
    scores = []
    cur = 0
    code_lines = code.splitlines()
    for line in range(len(code_lines)):
        scores.append([cur])
        for character in range(len(code_lines[line])):
            if code_lines[line][character] == "(":
                cur += 1
            elif code_lines[line][character] == ")":
                cur -= 1
            scores[line].append(cur)
    return scores


def get_before_token(
    code: str,
    line_no: int,
    char_no: int,
) -> str:
    code_lines = code.splitlines(keepends=True)
    j = 0
    for i in range(line_no):
        j += len(code_lines[i])
    j += char_no
    j -= 1  # start by go to last character before cursor position

    while j > -1 and not code[j].isspace():
        j -= 1
    while j > -1 and code[j].isspace():
        j -= 1

    word_chars = []
    while j > -1 and not code[j].isspace():
        word_chars.append(code[j])
        j -= 1
    word_chars.reverse()
    word = "".join(word_chars)
    return word
