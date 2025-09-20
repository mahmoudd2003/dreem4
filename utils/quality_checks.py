# utils/quality_checks.py
# -*- coding: utf-8 -*-
"""
Quality heuristics:
1) find_filler(text): returns a list of filler phrases found.
2) repetition_score(text): ratio of repeated sentences.
3) has_sensory(text): detects presence of sensory words.
4) quality_report(text): JSON with filler_count, repetition_ratio, has_sensory_language, filler_samples
   + extended checks: has_people_first, has_methodology, has_cases_section, has_sources_section,
     has_ibn_sirin_page, has_nabulsi_page, has_psych_ref
"""

import re
from typing import List, Dict

_FILLERS = [
    "ومن الجدير بالذكر",
    "لا يخفى على أحد",
    "يجدر الإشارة",
    "وفي هذا السياق",
    "الجدير بالذكر",
    "كما أسلفنا الذكر",
    "كما ذكرنا سابقًا",
    "الجدير بالإشارة",
    "ومن ناحية أخرى",
    "بوجه عام",
]

_SENSORY = [
    "بريق","رهبة","طمأنينة","قشعريرة","خفقان","دفء","برودة","صدى","نعومة","وخز",
    "ارتجاف","انقباض","سكينة","هدوء","انشراح","توتر"
]

_SENT_SPLIT = re.compile(r"[.!?؟؛\n]+")

def _normalize(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s

def find_filler(text: str) -> List[str]:
    t = text or ""
    found = []
    for f in _FILLERS:
        if f in t:
            found.append(f)
    return found

def repetition_score(text: str) -> float:
    t = text or ""
    sentences = [ _normalize(s) for s in _SENT_SPLIT.split(t) if _normalize(s) ]
    if not sentences:
        return 0.0
    seen = {}
    for s in sentences:
        seen[s] = seen.get(s, 0) + 1
    duplicates = sum(c-1 for c in seen.values() if c > 1)
    return round(duplicates / max(1, len(sentences)), 3)

def has_sensory(text: str) -> bool:
    t = text or ""
    return any(w in t for w in _SENSORY)

def quality_report(text: str) -> Dict:
    fillers = find_filler(text)
    rep = repetition_score(text)
    sensory = has_sensory(text)
    report = {
        "filler_count": len(fillers),
        "repetition_ratio": rep,
        "has_sensory_language": bool(sensory),
        "filler_samples": fillers[:5],
    }
    # Extended checks
    report.update(_extended_structure_and_sources(text))
    return report

# -----------------------------
# Extended checks for sources and structure
# -----------------------------
_SRC_IBN_SIRIN_PAGE_RE = re.compile(r"ابن\s*سيرين.*?(?:ص|صفحة)\s*\d+", re.IGNORECASE)
_SRC_NABULSI_PAGE_RE   = re.compile(r"النابلسي.*?(?:ص|صفحة)\s*\d+", re.IGNORECASE)
_SRC_PSYCH_RE          = re.compile(r"([اأإآء-يA-Za-z]+)\s*\(\s*(\d{4})\s*\)", re.UNICODE)

def check_sources(text: str) -> dict:
    t = text or ""
    return {
        "has_ibn_sirin_page": bool(_SRC_IBN_SIRIN_PAGE_RE.search(t)),
        "has_nabulsi_page":   bool(_SRC_NABULSI_PAGE_RE.search(t)),
        "has_psych_ref":      bool(_SRC_PSYCH_RE.search(t)),
    }

def _has_heading(text: str, keyword: str) -> bool:
    pat = re.compile(rf'^\s*#{{2,3}}\s*.*{re.escape(keyword)}.*$', re.MULTILINE)
    return bool(pat.search(text or ""))

def _people_first_present(text: str) -> bool:
    return _has_heading(text, "الخلاصة") or _has_heading(text, "الخلاصة السريعة")

def _methodology_present(text: str) -> bool:
    return _has_heading(text, "كيف نفسّر")

def _cases_present(text: str) -> bool:
    return _has_heading(text, "الحالات المؤثرة") or ("ورقي" in (text or "") and "معدني" in (text or ""))

def _sources_section_present(text: str) -> bool:
    return _has_heading(text, "المصادر")

def _extended_structure_and_sources(text: str) -> Dict:
    base = check_sources(text)
    base.update({
        "has_people_first": _people_first_present(text),
        "has_methodology": _methodology_present(text),
        "has_cases_section": _cases_present(text),
        "has_sources_section": _sources_section_present(text),
    })
    return base
