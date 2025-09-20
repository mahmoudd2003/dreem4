# utils/text_cleanup.py
# -*- coding: utf-8 -*-
"""
Filters to reduce flowery/metaphorical filler language.
Use remove_filler_phrases(text) before exporting.
"""
import re
from typing import Tuple, Dict

# Common metaphorical/filler patterns and pragmatic replacements
REPLACEMENTS = {
    # "كأن ... الأمل"
    r"كأن[^.\n\r]{0,60}الأمل": "قد يعكس ذلك شعورًا بالتفاؤل",
    # heaviness on chest
    r"كأن[^.\n\r]{0,80}ثقل[^.\n\r]{0,40}(?:صدره|على صدره|على صدرها)": "قد يشير ذلك إلى ضغط نفسي أو قلق",
    # shadows chasing
    r"كأن[^.\n\r]{0,80}الظلال[^.\n\r]{0,40}(?:تلاحق(?:ه|ها)|تتبعه)": "قد يرمز ذلك إلى خوفٍ من فقدان السيطرة",
    # generic phrases
    r"\bبريق\s*الأمل\b": "قد يشير إلى عودة الحافز أو تحسّن المزاج",
    r"\bثقل\s*العالم\b": "قد يدل على أعباء ومسؤوليات متراكمة",
    r"\bغرق(?:ت)?\s*في\s*بحر\s*من\s*الأفكار\b": "قد يعني اجترارًا فكريًا زائدًا",
}

def remove_filler_phrases(text: str) -> str:
    """Replace metaphorical clichés with pragmatic, interpretable sentences."""
    t = text or ""
    for pattern, repl in REPLACEMENTS.items():
        t = re.sub(pattern, repl, t, flags=re.IGNORECASE | re.UNICODE)
    return t

def remove_with_report(text: str) -> Tuple[str, Dict[str, int]]:
    """Return cleaned text and a usage report of which patterns were replaced."""
    t = text or ""
    counts = {}
    for pattern, repl in REPLACEMENTS.items():
        new_t, n = re.subn(pattern, repl, t, flags=re.IGNORECASE | re.UNICODE)
        if n:
            counts[pattern] = n
        t = new_t
    return t, counts
