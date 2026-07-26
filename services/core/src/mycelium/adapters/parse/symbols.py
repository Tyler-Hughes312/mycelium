"""Cheap-path symbol extraction (AD-8) for Py / TS / JS / Go."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from mycelium.adapters.git.files import language_for


@dataclass(frozen=True)
class SymbolRecord:
    path: str
    name: str
    kind: str
    language: str
    start_line: int
    end_line: int

    @property
    def node_id(self) -> str:
        return f"symbol:{self.path}:{self.name}:{self.start_line}"


_TS_JS_PATTERNS = [
    (
        "function",
        re.compile(
            r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(",
            re.MULTILINE,
        ),
    ),
    (
        "class",
        re.compile(
            r"^\s*(?:export\s+)?(?:abstract\s+)?class\s+(\w+)\b",
            re.MULTILINE,
        ),
    ),
    (
        "const",
        re.compile(
            r"^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?(?:\(|function\b)",
            re.MULTILINE,
        ),
    ),
]

_GO_FUNC = re.compile(r"^func\s+(?:\([^)]+\)\s*)?(\w+)\s*\(", re.MULTILINE)
_GO_TYPE = re.compile(r"^type\s+(\w+)\s+(?:struct|interface|func|\w)", re.MULTILINE)


def extract_symbols(repo_path: Path, rel_path: Path, source: str) -> list[SymbolRecord]:
    lang = language_for(rel_path)
    if lang is None:
        return []
    path_str = rel_path.as_posix()
    if lang == "python":
        return _python_symbols(path_str, source)
    if lang in {"typescript", "javascript"}:
        return _regex_symbols(path_str, lang, source, _TS_JS_PATTERNS)
    if lang == "go":
        return _go_symbols(path_str, source)
    return []


def _python_symbols(path_str: str, source: str) -> list[SymbolRecord]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    rows: list[SymbolRecord] = []

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            rows.append(
                SymbolRecord(
                    path=path_str,
                    name=node.name,
                    kind="function",
                    language="python",
                    start_line=int(node.lineno),
                    end_line=int(getattr(node, "end_lineno", node.lineno) or node.lineno),
                )
            )
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            rows.append(
                SymbolRecord(
                    path=path_str,
                    name=node.name,
                    kind="function",
                    language="python",
                    start_line=int(node.lineno),
                    end_line=int(getattr(node, "end_lineno", node.lineno) or node.lineno),
                )
            )
            self.generic_visit(node)

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            rows.append(
                SymbolRecord(
                    path=path_str,
                    name=node.name,
                    kind="class",
                    language="python",
                    start_line=int(node.lineno),
                    end_line=int(getattr(node, "end_lineno", node.lineno) or node.lineno),
                )
            )
            self.generic_visit(node)

    Visitor().visit(tree)
    return rows


def _line_span(source: str, start_idx: int) -> tuple[int, int]:
    start_line = source.count("\n", 0, start_idx) + 1
    rest = source[start_idx:].splitlines()
    end_line = start_line
    for i, line in enumerate(rest[1:41], start=1):
        end_line = start_line + i
        if i > 1 and not line.strip():
            break
    return start_line, end_line


def _regex_symbols(
    path_str: str,
    language: str,
    source: str,
    patterns: list[tuple[str, re.Pattern[str]]],
) -> list[SymbolRecord]:
    rows: list[SymbolRecord] = []
    seen: set[tuple[str, int]] = set()
    for kind, pattern in patterns:
        for match in pattern.finditer(source):
            name = match.group(1)
            start_line, end_line = _line_span(source, match.start())
            key = (name, start_line)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                SymbolRecord(
                    path=path_str,
                    name=name,
                    kind=kind,
                    language=language,
                    start_line=start_line,
                    end_line=end_line,
                )
            )
    return rows


def _go_symbols(path_str: str, source: str) -> list[SymbolRecord]:
    patterns = [("function", _GO_FUNC), ("type", _GO_TYPE)]
    return _regex_symbols(path_str, "go", source, patterns)
