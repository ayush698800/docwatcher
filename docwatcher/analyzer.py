"""
analyzer.py
===========
Parses Python and JavaScript/TypeScript source files using Tree-sitter to
extract top-level symbols (functions and classes).

Compares old vs new versions of a file to produce a list of ChangedSymbol
objects — only symbols whose source code actually changed.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

# ---- Tree-sitter language setup ----
try:
    import tree_sitter_python as tspython
    from tree_sitter import Language, Parser as TSParser
    PY_LANGUAGE = Language(tspython.language())
    _TS_AVAILABLE = True
except ImportError:
    _TS_AVAILABLE = False
    logger.warning("tree-sitter-python not available. Python symbol extraction disabled.")

try:
    import tree_sitter_javascript as tsjavascript
    from tree_sitter import Language, Parser as TSParser
    JS_LANGUAGE = Language(tsjavascript.language())
    _TS_JS_AVAILABLE = True
except ImportError:
    _TS_JS_AVAILABLE = False
    logger.warning("tree-sitter-javascript not available. JS symbol extraction disabled.")


@dataclass
class ChangedSymbol:
    """Represents a single function or class whose code changed between revisions."""
    name: str
    symbol_type: str       # 'function' or 'class'
    file_path: str
    old_code: str          # Source at HEAD~10 (empty string if new symbol)
    new_code: str          # Current source


def _get_parser_and_language(file_path: str):
    """
    Return the appropriate (Parser, Language) pair for a given file extension.
    Returns (None, None) for unsupported types.
    """
    if not _TS_AVAILABLE and not _TS_JS_AVAILABLE:
        return None, None

    if file_path.endswith('.py') and _TS_AVAILABLE:
        return TSParser(PY_LANGUAGE), PY_LANGUAGE
    elif file_path.endswith(('.js', '.ts')) and _TS_JS_AVAILABLE:
        return TSParser(JS_LANGUAGE), JS_LANGUAGE

    return None, None


def _extract_symbols(source_code: str, language, parser) -> dict:
    """
    Parse source_code and return a dict of {symbol_name: full_source_text}.
    Captures both function_definition and class_definition nodes.
    """
    if not source_code or not source_code.strip():
        return {}

    try:
        tree = parser.parse(bytes(source_code, 'utf-8'))
        root = tree.root_node
        symbols = {}

        def walk(node):
            # Match function definitions and class definitions
            if node.type in ('function_definition', 'class_definition',
                             'function_declaration', 'class_declaration',
                             'method_definition'):
                for child in node.children:
                    if child.type == 'identifier':
                        name = child.text.decode('utf-8')
                        symbols[name] = source_code[node.start_byte:node.end_byte]
                        break
            for child in node.children:
                walk(child)

        walk(root)
        return symbols

    except Exception as e:
        logger.debug(f"Symbol extraction failed: {e}")
        return {}


def get_changed_symbols(file_path: str, old_content: str, new_content: str) -> List[ChangedSymbol]:
    """
    Compare old_content vs new_content for the given file.

    Returns a list of ChangedSymbol for every symbol that:
      - is new (didn't exist before), or
      - has a different implementation than before.

    Symbols that are identical are skipped (no false positives).
    """
    parser, language = _get_parser_and_language(file_path)
    if parser is None:
        logger.debug(f"No parser available for {file_path}")
        return []

    old_symbols = _extract_symbols(old_content, language, parser) if old_content else {}
    new_symbols = _extract_symbols(new_content, language, parser) if new_content else {}

    changed = []
    for name, new_code in new_symbols.items():
        old_code = old_symbols.get(name, '')

        # Skip symbols that haven't changed at all
        if old_code.strip() == new_code.strip():
            continue

        symbol_type = 'class' if ('class ' in new_code[:30]) else 'function'
        changed.append(ChangedSymbol(
            name=name,
            symbol_type=symbol_type,
            file_path=file_path,
            old_code=old_code,
            new_code=new_code
        ))

    logger.debug(f"Found {len(changed)} changed symbols in {file_path}")
    return changed
