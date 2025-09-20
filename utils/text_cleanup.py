# utils/text_cleanup.py
# -*- coding: utf-8 -*-
"""
Expanded filler/metaphor filter.
- Rewrites ANY sentence containing "كأن" (simile) into a pragmatic line.
- Normalizes common rhetorical imagery (بحر من..، جبل من..، بريق الأمل..).
Use: remove_filler_phrases(text) before export or via the "تنظيف الحسّي/المجازي" button.
"""
import re
from typing import Tuple, Dict

# Targeted imagery replacements (case-insensitive)
REPLACEMENTS = {
    r"\bبريق\s*الأمل\b": "قد يشير ذلك إلى عودة الحافز أو تحسّن المزاج",
    r"\bثقل\s*العالم\b": "قد يدل على أعباء ومسؤوليات متراكمة",
    r"\bغرق(?:ت)?\s*في\s*بحر\s*من\s*الأفكار\b": "قد يعني اجترارًا فكريًا زائدًا",
    r"\bجبل\s*من\s*الهموم\b": "قد يدل على تراكم الضغوط",
    r"\bسيول\s*من\s*المشاعر\b": "قد يعكس فيضًا عاطفيًا صعب التنظيم",
    r"\bظلال\s*الخوف\b": "قد يرمز إلى قلقٍ مستمر",
}

# Sentence splitter (Arabic + Latin punctuation)
_SENT_SPLIT = re.compile(r"([^\.!\?؟؛\n]+[\.!\?؟؛]?)", re.UNICODE)

def _rewrite_kaanna_sentence(sentence: str) -> str:
    """Convert sentences containing 'كأن' into pragmatic interpretation."""
    s = sentence.strip()
    if not s:
        return s
    trail = s[-1] if s and s[-1] in ".!؟؛…" else ""
    return "قد يشير ذلك إلى انطباع أو قياس نفسي يرتبط بسياق الرائي" + (trail or "")

def _aggressive_simile_pass(text: str):
    """Replace ANY sentence containing 'كأن' with a pragmatic rewrite. Returns (new_text, count)."""
    parts = _SENT_SPLIT.findall(text or "")
    out = []
    n = 0
    for sent in parts:
        if "كأن" in sent:
            out.append(_rewrite_kaanna_sentence(sent))
            n += 1
        else:
            out.append(sent)
    return "".join(out), n

def remove_filler_phrases(text: str) -> str:
    """Aggressive cleanup: replace similes + imagery clichés with pragmatic lines."""
    t = text or ""
    # 1) Aggressive 'كأن' pass
    t, _ = _aggressive_simile_pass(t)
    # 2) Imagery replacements
    for pattern, repl in REPLACEMENTS.items():
        t = re.sub(pattern, repl, t, flags=re.IGNORECASE | re.UNICODE)
    # 3) Minor whitespace tidy
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t

def remove_with_report(text: str):
    """Return cleaned text and a report of applied replacements, including 'كأن' counter."""
    t = text or ""
    report = {}

    # Aggressive 'كأن' pass
    t, n_kaan = _aggressive_simile_pass(t)
    if n_kaan:
        report["kaanna_sentences_rewritten"] = n_kaan

    # Imagery replacements with counts
    for pattern, repl in REPLACEMENTS.items():
        new_t, n = re.subn(pattern, repl, t, flags=re.IGNORECASE | re.UNICODE)
        if n:
            report[pattern] = n
        t = new_t

    # Tidy
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t, report
