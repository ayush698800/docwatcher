from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from docwatcher.diff_parser import ChangedFile, get_changed_files
from docwatcher.embeddings import search_docs
from docwatcher.llm_checker import check_consistency, is_lm_studio_running
from docwatcher.symbol_extractor import ChangedSymbol, get_changed_symbols


@dataclass
class AnalysisResult:
    changed_files: List[ChangedFile] = field(default_factory=list)
    changed_symbols: List[ChangedSymbol] = field(default_factory=list)
    errors: List[Tuple[object, ChangedSymbol]] = field(default_factory=list)
    warnings: List[Tuple[object, ChangedSymbol]] = field(default_factory=list)
    infos: List[Tuple[object, ChangedSymbol, List[dict]]] = field(default_factory=list)
    undocumented: List[ChangedSymbol] = field(default_factory=list)
    llm_available: bool = False


def collect_changed_symbols(repo_path: str = ".") -> tuple[List[ChangedFile], List[ChangedSymbol]]:
    changed_files = get_changed_files(repo_path)
    changed_symbols: List[ChangedSymbol] = []

    for changed_file in changed_files:
        changed_symbols.extend(
            get_changed_symbols(
                changed_file.path,
                changed_file.old_content,
                changed_file.new_content,
            )
        )

    return changed_files, changed_symbols


def analyze_repo(repo_path: str = ".", use_llm: bool = True) -> AnalysisResult:
    changed_files, changed_symbols = collect_changed_symbols(repo_path)
    llm_available = is_lm_studio_running(repo_path) if use_llm else False

    result = AnalysisResult(
        changed_files=changed_files,
        changed_symbols=changed_symbols,
        llm_available=llm_available,
    )

    for symbol in changed_symbols:
        matches = search_docs(repo_path, symbol.name)
        if not matches:
            result.undocumented.append(symbol)
            continue

        if not llm_available:
            result.infos.append((None, symbol, matches))
            continue

        for match in matches:
            verdict = check_consistency(
                symbol_name=symbol.name,
                old_code=symbol.old_code,
                new_code=symbol.new_code,
                doc_content=match["content"],
                doc_file=match["source_file"],
                doc_line=match["start_line"],
                doc_heading=match["heading"],
                repo_path=repo_path,
            )
            if not verdict or not verdict.stale:
                continue
            if verdict.severity == "error":
                result.errors.append((verdict, symbol))
            elif verdict.severity == "warning":
                result.warnings.append((verdict, symbol))
            else:
                result.infos.append((verdict, symbol, matches))

    return result
