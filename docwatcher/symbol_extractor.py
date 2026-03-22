from dataclasses import dataclass
from typing import List
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
from tree_sitter import Language, Parser

PY_LANGUAGE = Language(tspython.language())
JS_LANGUAGE = Language(tsjavascript.language())

@dataclass
class ChangedSymbol:
    name: str
    symbol_type: str
    file_path: str
    old_code: str
    new_code: str

def get_parser(file_path: str):
    if file_path.endswith('.py'):
        parser = Parser(PY_LANGUAGE)
        return parser, PY_LANGUAGE
    elif file_path.endswith('.js'):
        parser = Parser(JS_LANGUAGE)
        return parser, JS_LANGUAGE
    return None, None

def extract_symbols(source_code: str, language, parser) -> dict:
    tree = parser.parse(bytes(source_code, 'utf-8'))
    root = tree.root_node
    symbols = {}

    def walk(node):
        if node.type in ('function_definition', 'class_definition'):
            for child in node.children:
                if child.type == 'identifier':
                    name = child.text.decode('utf-8')
                    symbols[name] = source_code[node.start_byte:node.end_byte]
                    break
        for child in node.children:
            walk(child)

    walk(root)
    return symbols

def get_changed_symbols(file_path: str, old_content: str, new_content: str) -> List[ChangedSymbol]:
    parser, language = get_parser(file_path)
    if not parser:
        return []

    old_symbols = extract_symbols(old_content, language, parser) if old_content else {}
    new_symbols = extract_symbols(new_content, language, parser) if new_content else {}

    changed = []

    for name, new_code in new_symbols.items():
        old_code = old_symbols.get(name, '')
        if old_code != new_code:
            symbol_type = 'function' if 'def ' in new_code or 'function ' in new_code else 'class'
            changed.append(ChangedSymbol(
                name=name,
                symbol_type=symbol_type,
                file_path=file_path,
                old_code=old_code,
                new_code=new_code
            ))

    return changed