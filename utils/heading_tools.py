# utils/heading_tools.py
# -*- coding: utf-8 -*-
from typing import List, Dict, Tuple
import re

H2_RE = re.compile(r'^\s*##\s+(.+?)\s*$', re.MULTILINE)
H3_RE = re.compile(r'^\s*###\s+(.+?)\s*$', re.MULTILINE)

def _find_h2(text: str) -> List[str]:
    return [m.group(1).strip() for m in H2_RE.finditer(text or "")]

def _find_h3(text: str) -> List[str]:
    return [m.group(1).strip() for m in H3_RE.finditer(text or "")]

def enforce_outline(text: str, required_h2: List[str], required_h3_map: Dict[str, List[str]]) -> str:
    text = text or ""
    existing_h2 = _find_h2(text)
    existing_h3 = _find_h3(text)
    if not text.endswith("\n"):
        text += "\n"

    tail_additions = []
    for h2 in required_h2:
        if h2 not in existing_h2:
            tail_additions.append(f"\n## {h2}\n- (Placeholder) أضف نقاطًا موجزة هنا.\n")

    for parent, subs in (required_h3_map or {}).items():
        if not subs or parent not in existing_h2:
            continue
        missing_subs = [s for s in subs if s not in existing_h3]
        if not missing_subs:
            continue
        parts = re.split(r'(?m)^(## .+)$', text)
        rebuilt = []
        i = 0
        while i < len(parts):
            if i + 1 < len(parts) and parts[i+1].lstrip().startswith("## "):
                pre = parts[i]; h2_line = parts[i+1]; section = parts[i+2] if i+2 < len(parts) else ""
                if h2_line.strip()[3:] == parent:
                    inject = "".join([f"### {sub}\n- (Placeholder) نقطة موجزة.\n" for sub in missing_subs])
                    section = inject + section
                rebuilt.extend([pre, h2_line, section]); i += 3
            else:
                rebuilt.append(parts[i]); i += 1
        text = "".join(rebuilt)

    if tail_additions:
        text = text.rstrip() + "\n" + "\n".join(tail_additions) + "\n"
    return text

def default_required(symbol: str = "") -> Tuple[List[str], Dict[str, List[str]]]:
    required_h2 = [
        "الخلاصة السريعة",
        "كيف نفسّر؟",
        "الحالات المؤثرة",
        "حالة الرائي",
        "مقارنة التراث والنفسي",
        "FAQ",
        "المصادر",
    ]
    required_h3_map = { "حالة الرائي": ["عزباء","متزوجة","حامل","مطلقة","رجل"] }
    s = (symbol or "").strip()
    if s in ("المال","مال","النقود","النقد"):
        required_h3_map["الحالات المؤثرة"] = ["مال ورقي vs معدني","العثور","الضياع","السرقة","الإهداء","العدّ","التبرّع","المبلغ والعملة"]
    else:
        required_h3_map["الحالات المؤثرة"] = ["تنويعات شائعة","سياقات تزيد/تنقص المعنى"]
    return required_h2, required_h3_map
