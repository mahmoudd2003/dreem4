# utils/quality_checks.py
# -*- coding: utf-8 -*-
"""
Quality heuristics + structure/source checks + FAQ checks.

APIs:
- find_filler(text) -> list[str]
- repetition_score(text) -> float
- has_sensory(text) -> bool
- quality_report(text) -> dict
- check_sources(text) -> dict (flags)
- source_problems(text) -> list[str] (explicit requirements problems)
- check_faq_quality(faq_list_or_json) -> list[str]
"""
import re
import json
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
    return [f for f in _FILLERS if f in t]

def repetition_score(text: str) -> float:
    t = text or ""
    sentences = [_normalize(s) for s in _SENT_SPLIT.split(t) if _normalize(s)]
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

# -----------------------------
# Sources & structure presence flags
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
    return _has_heading(text, "منهجية التفسير") or _has_heading(text, "كيف نفسّر")

def _cases_present(text: str) -> bool:
    return _has_heading(text, "الحالات المؤثرة") or ("ورقي" in (text or "") and "معدني" in (text or ""))

def _sources_section_present(text: str) -> bool:
    return _has_heading(text, "المصادر")

# -----------------------------
# FAQ checks
# -----------------------------
def _sentence_count(ar_text: str) -> int:
    if not ar_text:
        return 0
    parts = re.split(r"[\.!\?؟؛]\s*", ar_text.strip())
    return len([p for p in parts if p.strip()])

def check_faq_quality(faq_list):
    """
    Accepts:
      - list of dicts: [{"q": "...", "a": "..."}, ...]
      - list of tuples: [(q, a), ...]
      - JSON string with {"faq": [...]}
    Returns list of problems.
    """
    problems = []
    items = []

    if isinstance(faq_list, str):
        try:
            data = json.loads(faq_list)
            items = data.get("faq", [])
        except Exception:
            items = []
    else:
        items = faq_list or []

    norm = []
    for it in items:
        if isinstance(it, dict):
            q = it.get("q") or it.get("question") or ""
            a = it.get("a") or it.get("answer") or ""
            norm.append((q, a))
        elif isinstance(it, (list, tuple)) and len(it) >= 2:
            norm.append((it[0], it[1]))

    if len(norm) < 5:
        problems.append("FAQ أقل من 5 أسئلة")

    for q, a in norm:
        if _sentence_count(a) < 3:
            problems.append(f"الإجابة على '{q[:25]}...' قصيرة (< 3 جمل)")

    return problems

# -----------------------------
# Source problems (explicit requirement list)
# -----------------------------
def source_problems(text: str):
    """
    Check explicit presence of required sources/fields.
    - ابن سيرين / النابلسي / ابن شاهين
    - mention of page numbers (ص or صفحة)
    - modern psych ref with a year like (2020) or 'سنة'
    """
    t = text or ""
    req = ["ابن سيرين", "النابلسي", "ابن شاهين"]
    probs = []
    for r in req:
        if r not in t:
            probs.append(f"المصدر {r} غير مذكور")
    if ("ص" not in t) and ("صفحة" not in t):
        probs.append("لم تُذكر أرقام الصفحات من كتب التراث")
    if not re.search(r"\(\s*20\d{2}\s*\)", t) and ("سنة" not in t):
        probs.append("لا يوجد مرجع نفسي حديث بسنة نشر")
    return probs

# -----------------------------
# Master report
# -----------------------------
def quality_report(text: str) -> Dict:
    fillers = find_filler(text)
    rep = repetition_score(text)
    sensory = has_sensory(text)
    flags = check_sources(text)
    report: Dict = {
        "filler_count": len(fillers),
        "repetition_ratio": rep,
        "has_sensory_language": bool(sensory),
        "filler_samples": fillers[:5],
        "has_people_first": _people_first_present(text),
        "has_methodology": _methodology_present(text),
        "has_cases_section": _cases_present(text),
        "has_sources_section": _sources_section_present(text),
        **flags,
        "source_problems": source_problems(text),
    }
    return report
