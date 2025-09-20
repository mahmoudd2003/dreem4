# utils/meta_generator.py
# -*- coding: utf-8 -*-
"""
Meta/FAQ generator using llm() and JSON-LD builder.
"""

import json
from typing import Dict, Any, List
from utils.openai_client import llm

PROMPTS_DIR = "prompts"

def _read_prompt_file(rel_path: str) -> str:
    path = f"{PROMPTS_DIR}/{rel_path}"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def generate_meta_and_faq(article: str, primary_kw: str) -> Dict[str, Any]:
    """Call LLM with prompts/meta_faq.txt and return {title, description, faq} JSON with basic error handling."""
    tpl = _read_prompt_file("meta_faq.txt")
    prompt = tpl.format(text=article, primary_kw=primary_kw)
    raw = llm(prompt, temperature=0.2, max_tokens=500)
    try:
        data = json.loads(raw)
        if "faq" in data and isinstance(data["faq"], list):
            cleaned = []
            for item in data["faq"]:
                if isinstance(item, dict):
                    q = item.get("q") or item.get("question") or ""
                    a = item.get("a") or item.get("answer") or ""
                    if q and a:
                        cleaned.append({"q": q, "a": a})
            data["faq"] = cleaned
        return data
    except Exception:
        return {
            "title": "",
            "description": "",
            "faq": [],
            "_warning": "تعذّر تحليل JSON تلقائيًا. يرجى المراجعة اليدوية للناتج.",
            "_raw": raw
        }

# -----------------------------
# JSON-LD builder (E-E-A-T metadata)
# -----------------------------

def _safe_text(x):
    return (x or "").strip() if isinstance(x, str) else ""

def build_jsonld(article_text: str,
                 meta: Dict[str, Any],
                 author: Dict[str, str],
                 reviewer: Dict[str, str],
                 last_updated: str = "") -> Dict[str, Any]:
    """Build JSON-LD with Article + FAQPage + Author + reviewedBy."""
    title = _safe_text(meta.get("title"))
    description = _safe_text(meta.get("description"))
    faq = meta.get("faq") or []
    if not isinstance(faq, list):
        faq = []

    author_name = _safe_text(author.get("name"))
    author_creds = _safe_text(author.get("credentials"))
    reviewer_name = _safe_text(reviewer.get("name"))
    date_mod = _safe_text(last_updated)

    faq_entities: List[Dict[str, Any]] = []
    for item in faq:
        q = _safe_text(item.get("q")) if isinstance(item, dict) else ""
        a = _safe_text(item.get("a")) if isinstance(item, dict) else ""
        if q and a:
            faq_entities.append({
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer","text": a}
            })

    graph: List[Dict[str, Any]] = []

    article_node: Dict[str, Any] = {
        "@type": "Article",
        "headline": title or None,
        "description": description or None,
        "dateModified": date_mod or None,
    }
    if author_name:
        article_node["author"] = {"@type": "Person","name": author_name,"description": author_creds or None}
    if reviewer_name:
        article_node["reviewedBy"] = {"@type": "Person","name": reviewer_name}

    article_node = {k: v for k, v in article_node.items() if v is not None}
    graph.append(article_node)

    if faq_entities:
        graph.append({"@type": "FAQPage","mainEntity": faq_entities})

    return {"@context": "https://schema.org","@graph": graph}
