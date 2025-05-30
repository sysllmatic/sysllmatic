#!/usr/bin/env python3
import re
from typing import List, Tuple

# -- regular‑expressions -------------------------------------------------- #
RE_MAIN    = re.compile(r"\bint\s+main\s*\([^)]*\)\s*\{", re.S)
RE_ASSERT  = re.compile(r"\bassert\s*\([^;]*?;\s*", re.S)   # keeps semicolon & newline

def _extract_regions(code: str) -> Tuple[str, str]:
    """
    Return (prologue, body) where:
        * prologue – everything up to and including the opening '{' of main
        * body     – the content inside main { … }  (no closing brace)
    """
    m = RE_MAIN.search(code)
    if not m:
        raise ValueError("Could not find 'int main(...) {'")

    start_body = m.end()         # index just after the opening '{'
    depth = 1
    i = start_body
    while i < len(code) and depth:
        if   code[i] == '{':
            depth += 1
        elif code[i] == '}':
            depth -= 1
        i += 1
    if depth:
        raise ValueError("Unbalanced braces in main()")

    prologue = code[:start_body]
    body     = code[start_body:i-1]      # drop final '}'
    return prologue, body

def _split_body(body: str) -> Tuple[str, List[str]]:
    """
    Return:
        * prefix   – code before the first assert (variable setups, etc.)
        * asserts  – list of each assert statement as strings (semicolon kept)
    """
    first = RE_ASSERT.search(body)
    if not first:
        raise ValueError("No assert(...) found in main()")

    prefix  = body[:first.start()]
    asserts = [m.group(0) for m in RE_ASSERT.finditer(body)]
    return prefix, asserts

def split_asserts(test_code: str) -> List[str]:
    """
    Convert a single test_code block with many asserts into
    a list of *complete* test_code snippets, one per assert.

    Returns
    -------
    snippets : list[str]   # ready‑to‑compile code strings
    """
    prologue, body = _extract_regions(test_code)
    prefix, asserts = _split_body(body)

    snippets: List[str] = []
    for a in asserts:
        snippet = prologue + prefix + a + "\n}\n"
        snippets.append(snippet)
    return snippets