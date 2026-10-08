"""
F-001 (CWE-79): the web interface must show text as text.

Server and user text (host names, error messages) must never be parsed as HTML. The reliable way is to
not use the APIs that parse HTML at all: `textContent` and DOM nodes cannot turn text into markup, while
every `innerHTML` that receives data is one forgotten `escapeHtml()` away from an injection.

This is a static check of the script. It does not execute it; the behaviour was also checked in a
browser (docs/security/F-001-xss-innerhtml.md).
"""
import re
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "static" / "script.js"

# APIs that parse a string as HTML or as code
HTML_SINKS = {
    "innerHTML": r"\.innerHTML\b",
    "outerHTML": r"\.outerHTML\b",
    "insertAdjacentHTML": r"\binsertAdjacentHTML\s*\(",
    "document.write": r"\bdocument\.write(ln)?\s*\(",
    "createContextualFragment": r"\bcreateContextualFragment\s*\(",
    "eval": r"\beval\s*\(",
    "new Function": r"\bnew\s+Function\s*\(",
}


@pytest.mark.parametrize("name", HTML_SINKS)
def test_script_does_not_use_html_parsing_apis(name):
    lines = SCRIPT.read_text().splitlines()
    hits = [f"line {number}: {line.strip()[:80]}" for number, line in enumerate(lines, 1)
            if re.search(HTML_SINKS[name], line)]
    assert not hits, f"{name} turns text into markup (F-001):\n" + "\n".join(hits)


def test_script_builds_nodes_instead_of_html():
    # guards against the test above passing only because the script was emptied or renamed
    text = SCRIPT.read_text()
    assert "createElement" in text
    assert "textContent" in text or ".append(" in text
