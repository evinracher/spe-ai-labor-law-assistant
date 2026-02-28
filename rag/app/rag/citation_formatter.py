"""
Citation Formatter
==================

Utility for cleaning up verbose citation references that the LLM embeds in its
answer text.  The RAG pipeline instructs Gemini to cite sources using raw
document metadata, which results in long Windows-style paths such as:

    (d:\\Proyectos Especializacion\\...\\DECRETO 1072 DE 2015.pdf,
     Página: 20, Fragmento: chunk_108)

This module replaces every such reference with a concise human-readable form:

    (DECRETO 1072 DE 2015, Pág: 20)

Usage
-----
    from app.rag.citation_formatter import format_citations_in_text

    clean_answer = format_citations_in_text(raw_answer)
"""

from __future__ import annotations

import os
import re

from langchain_core.tools import tool

# ---------------------------------------------------------------------------
# Regex pattern
# ---------------------------------------------------------------------------
# Matches a citation block like:
#   (some/path/or\windows\path\FILENAME.pdf, Página: 20, Fragmento: chunk_X[, chunk_Y…])
#
# Capture groups:
#   1 → full path ending in .pdf   (used to extract the bare filename)
#   2 → page number
#
# Notes:
#   • The path segment is greedy-but-bounded by `,` so it stops at the first
#     comma that follows the `.pdf`.
#   • `Fragmento:` block may list multiple comma-separated chunk ids; the
#     trailing `)` closes the whole citation.
#   • `re.IGNORECASE` handles "Página" / "página" / "PÁGINA" variations.
# ---------------------------------------------------------------------------
_CITATION_PATTERN = re.compile(
    r"\("  # opening paren
    r"([^()]*?\.pdf)"  # group 1: path ending in .pdf
    r",\s*[Pp]ágina:\s*(\d+)"  # group 2: page number
    r",\s*Fragmento:\s*[^)]*"  # chunk ids (discarded)
    r"\)",  # closing paren
    re.IGNORECASE,
)


@tool
def format_citations_in_text(text: str) -> str:
    """Replace verbose path-based citations with short, readable references.

    Parameters
    ----------
    text:
        Raw answer text produced by the LLM, potentially containing one or
        more long citation references.

    Returns
    -------
    str
        The same text with every matching citation replaced by the compact
        ``(DOCUMENT NAME, Pág: N)`` format.

    Examples
    --------
    >>> raw = (
    ...     'Los trabajadores tienen derecho a vacaciones '
    ...     r'(d:\\path\\DECRETO 1072 DE 2015.pdf, Página: 20, Fragmento: chunk_108).'
    ... )
    >>> format_citations_in_text(raw)
    'Los trabajadores tienen derecho a vacaciones (DECRETO 1072 DE 2015, Pág: 20).'
    """

    def _replacer(match: re.Match) -> str:
        full_path: str = match.group(1)
        page: str = match.group(2)

        # Normalise separators so os.path.basename works on Windows paths
        # even when running on Linux/macOS.
        normalised = full_path.replace("\\", "/")
        filename = os.path.basename(normalised)
        name_without_ext = os.path.splitext(filename)[0]

        return f"({name_without_ext}, Pág: {page})"

    return _CITATION_PATTERN.sub(_replacer, text)
