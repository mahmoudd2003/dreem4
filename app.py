# app.py
# -*- coding: utf-8 -*-
"""
Streamlit app for generating Arabic dream-interpretation articles with People-first, methodology, and E-E-A-T.
Includes:
- Outline generation with enforced mandatory headings (H2/H3)
- People-first Summary (3 lines)
- Draft generation (with target length + methodology refs)
- Review/Improve
- Quality Report (heuristics + source/section flags)
- Quality Gate (LLM-based JSON)
- Meta/FAQ generation
- JSON-LD (Article + FAQPage + Author + reviewedBy)
- Balance Rewriter
- Human Touch
- Export DOCX/PDF with mandatory disclaimer
"""

import os
import json
import streamlit as st

from utils.openai_client import llm
from utils.quality_checks import quality_report
from utils.meta_generator import generate_meta_and_faq
from utils.exporters import to_docx, to_pdf
from utils.heading_tools import enforce_outline, default_required
from utils.enhanced_fix import ensure_disclaimer
from utils.text_cleanup import remove_filler_phrases
from utils.heading_tools import normalize_methodology_heading

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")

def _read_prompt(name: str) -> str:
    path = os.path.join(PROMPTS_DIR, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"ملف البرومبت غير موجود: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _format_prompt(tpl: str, **kwargs) -> str:
    try:
        return tpl.format(**kwargs)
    except Exception:
        addon = ["\n\n[المعطيات]"]
        for k, v in kwargs.items():
            addon.append(f"[{k.upper()}]: {v}")
        return tpl + "\n" + "\n".join(addon)

def _download_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def _init_state():
    defaults = {
        "outline": "",
        "draft": "",
        "reviewed": "",
        "meta_json": "",
        "humanized": "",
        "quality_gate_json": "",
        "balanced": "",
        "people_first": "",
        "cleaned": "",
        "expanded": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

st.set_page_config(page_title="نظام مقالات تفسير الأحلام", page_icon="🌙", layout="wide")
_init_state()

st.title("🌓 نظام كتابة مقالات تفسير الأحلام")
st.caption("People-first + منهجية واضحة + E-E-A-T | Python + Streamlit + OpenAI")

with st.sidebar:
    st.header("الإعدادات")
    st.markdown("- تأكد من وجود ملف `.env` يحوي `OPENAI_API_KEY`.")
    st.markdown("- يمكن ضبط الموديل عبر `LLM_MODEL` في `.env`.")
    temp = st.slider("Temperature", 0.0, 1.2, 0.4, 0.05, help="درجة التنوع في الإخراج")
    max_tokens = st.number_input("Max tokens", min_value=200, max_value=4000, value=1800, step=50)
    st.divider()
    st.markdown("**البرومبتات المستخدمة:**")
    st.code(
        "prompts/outline.txt\n"
        "prompts/people_first_summary.txt\n"
        "prompts/draft.txt\n"
        "prompts/review.txt\n"
        "prompts/meta_faq.txt\n"
        "prompts/human_touch.txt\n"
        "prompts/quality_gate.txt\n"
        "prompts/consistency_check.txt\n"
        "prompts/balance_rewriter.txt",
        language="bash"
    )

    st.subheader("المنهجية والمراجع")
    ibn_sirin_edition = st.text_input("طبعة ابن سيرين", value="")
    ibn_sirin_page    = st.text_input("صفحة ابن سيرين", value="")
    nabulsi_edition   = st.text_input("طبعة النابلسي", value="")
    nabulsi_page      = st.text_input("صفحة النابلسي", value="")
    psych_ref         = st.text_input("مرجع نفسي (عنوان/سنة/صفحة)", value="")

    st.subheader("E-E-A-T")
    author_name = st.text_input("اسم الكاتب (Author)", value="")
    author_credentials = st.text_input("اعتماد الكاتب/نبذة قصيرة", value="")
    reviewed_by = st.text_input("مراجَع من قِبل (خبير/اختياري)", value="")
    last_updated = st.text_input("تاريخ آخر تحديث (YYYY-MM-DD)", value="")

    st.subheader("طول المقال المستهدف")
    target_words = st.slider("عدد الكلمات (تقريبي)", 400, 2000, 1000, 50)

col1, col2 = st.columns([1,1])
with col1:
    symbol = st.text_input("🔣 الرمز (symbol)", key="inp_symbol", placeholder="مثال: الذهب، المطر، البحر")
    primary_kw = st.text_input("🔑 الكلمة المفتاحية الرئيسية (primary_kw)", key="inp_pk", placeholder="مثال: تفسير حلم الذهب")
with col2:
    related_kws = st.text_area("🧩 الكلمات المرتبطة (related_kws)", key="inp_rk", placeholder="افصل بينها بفواصل، مثال: تفسير حلم الذهب للعزباء، رؤية الذهب للمتزوجة")

article_area = st.text_area("📝 مساحة النص/المسودات", value=st.session_state.get("draft", ""), height=300, key="article_area")

st.divider()

# Actions
b1, b2, b3, b4, b5, b6, b7, b8, b9, b10, b11, b12 = st.columns(12)
gen_outline = b1.button("🧱 توليد المخطط")
do_pfs      = b2.button("👥 People-first Summary")
gen_draft   = b3.button("🧾 توليد المسودة")
do_review   = b4.button("🧹 مراجعة وتحسين")
do_quality  = b5.button("🔍 Quality Report")
do_qgate    = b6.button("✅ Quality Gate")
do_meta     = b7.button("🧭 Meta/FAQ (JSON)")
do_jsonld   = b8.button("🧾 JSON-LD")
do_balance  = b9.button("⚖️ Balance Rewriter")
do_human    = b10.button("👤 Human Touch")
exp_docx    = b11.button("⬇️ تصدير DOCX")
exp_pdf     = b12.button("⬇️ تصدير PDF")


st.divider()
c1, c2 = st.columns(2)
do_clean  = c1.button("🧽 تنظيف الحسّي/المجازي")
do_expand = c2.button("🧩 توسيع الحالات")


# Defensive guard
try:
    gen_outline; do_pfs; gen_draft; do_review; do_quality; do_qgate; do_meta; do_jsonld; do_balance; do_human; exp_docx; exp_pdf
except NameError:
    gen_outline = do_pfs = gen_draft = do_review = do_quality = do_qgate = do_meta = do_jsonld = do_balance = do_human = exp_docx = exp_pdf = False

# Generate Outline
if gen_outline:
    try:
        if not symbol or not primary_kw:
            st.warning("الرجاء إدخال الرمز والكلمة المفتاحية.")
        else:
            tpl = _read_prompt("outline.txt")
            prompt = _format_prompt(
                tpl,
                symbol=symbol,
                primary_kw=primary_kw,
                related_kws=related_kws,
                ibn_sirin_edition=ibn_sirin_edition,
                ibn_sirin_page=ibn_sirin_page,
                nabulsi_edition=nabulsi_edition,
                nabulsi_page=nabulsi_page,
                psych_ref=psych_ref,
            )
            outline = llm(prompt, temperature=temp, max_tokens=min(max_tokens, 1200)).strip()
            # Enforce required headings
            req_h2, req_h3 = default_required(symbol)
            outline = enforce_outline(outline, req_h2, req_h3)
            outline = normalize_methodology_heading(outline)
            st.session_state["outline"] = outline
            st.success("تم توليد المخطط بنجاح (مع فرض العناوين الأساسية).")
            st.text_area("📋 المخطط الناتج", value=st.session_state["outline"], height=300, key="outline_area")
    except Exception as e:
        st.error(f"فشل توليد المخطط: {e}")

# People-first Summary
if do_pfs:
    try:
        base = st.session_state.get("reviewed") or st.session_state.get("draft") or st.session_state.get("outline") or article_area
        if not base or not base.strip():
            st.warning("لا يوجد نص لبناء الخلاصة People-first.")
        else:
            tpl = _read_prompt("people_first_summary.txt")
            prompt = _format_prompt(tpl, article=base)
            pfs = llm(prompt, temperature=0.2, max_tokens=180)
            st.session_state["people_first"] = pfs.strip()
            st.success("تم توليد الخلاصة People-first.")
            st.text_area("👥 الخلاصة (3 أسطر)", value=st.session_state["people_first"], height=120, key="pfs_area")
    except Exception as e:
        st.error(f"فشل توليد خلاصة People-first: {e}")

# Generate Draft
if gen_draft:
    try:
        outline_src = st.session_state.get("outline") or ""
        if not outline_src:
            st.warning("لا يوجد مخطط. قم أولًا بتوليد المخطط.")
        else:
            tpl = _read_prompt("draft.txt")
            prompt = _format_prompt(
                tpl,
                outline=outline_src,
                people_first=st.session_state.get("people_first", ""),
                ibn_sirin_edition=ibn_sirin_edition,
                ibn_sirin_page=ibn_sirin_page,
                nabulsi_edition=nabulsi_edition,
                nabulsi_page=nabulsi_page,
                psych_ref=psych_ref,
                target_words=target_words,
            )
            draft = llm(prompt, temperature=temp, max_tokens=max_tokens).strip()
            st.session_state["draft"] = draft
            st.session_state["reviewed"] = ""
            st.success("تم توليد المسودة.")
            st.text_area("🧾 المسودة الناتجة", value=st.session_state["draft"], height=400, key="draft_area")
    except Exception as e:
        st.error(f"فشل توليد المسودة: {e}")

# Review
if do_review:
    try:
        base_text = st.session_state.get("reviewed") or st.session_state.get("draft") or article_area
        if not base_text or not base_text.strip():
            st.warning("لا يوجد نص للمراجعة. الصق نصًا في المساحة أو ولّد مسودة.")
        else:
            tpl = _read_prompt("review.txt")
            prompt = _format_prompt(tpl, text=base_text)
            improved = llm(prompt, temperature=0.2, max_tokens=max_tokens).strip()
            st.session_state["reviewed"] = improved
            st.success("تمت المراجعة والتحسين.")
            st.text_area("✨ النص بعد المراجعة", value=st.session_state["reviewed"], height=400, key="reviewed_area")
    except Exception as e:
        st.error(f"فشل المراجعة: {e}")

# Quality Report (heuristics)
if do_quality:
    try:
        target = st.session_state.get("reviewed") or st.session_state.get("draft") or article_area
        if not target or not target.strip():
            st.warning("لا يوجد نص لتحليل الجودة.")
        else:
            q = quality_report(target)
            st.json(q, expanded=False)
    except Exception as e:
        st.error(f"فشل فحص الجودة: {e}")

# Quality Gate (LLM-based JSON Report)
if do_qgate:
    try:
        target = st.session_state.get("humanized") or st.session_state.get("balanced") or st.session_state.get("reviewed") or st.session_state.get("draft") or article_area
        if not target or not target.strip():
            st.warning("لا يوجد نص لفحص Quality Gate.")
        else:
            tpl = _read_prompt("quality_gate.txt")
            prompt = _format_prompt(tpl, text=target)
            raw = llm(prompt, temperature=0.1, max_tokens=700)
            try:
                data = json.loads(raw)
                st.session_state["quality_gate_json"] = json.dumps(data, ensure_ascii=False, indent=2)
                st.json(data, expanded=False)
            except Exception:
                st.session_state["quality_gate_json"] = raw
                st.code(raw, language="json")
            st.success("تم تنفيذ Quality Gate.")
            if st.session_state.get("quality_gate_json"):
                try:
                    _qgate_bytes = st.session_state["quality_gate_json"].encode("utf-8")
                    st.download_button("💾 تنزيل تقرير Quality Gate (JSON)", data=_qgate_bytes, file_name="quality_gate.json", mime="application/json")
                except Exception as _e:
                    st.info(f"تعذّر تجهيز ملف التنزيل: {_e}")
    except Exception as e:
        st.error(f"فشل تنفيذ Quality Gate: {e}")

# Meta / FAQ (JSON) + JSON-LD
if do_meta:
    try:
        article = st.session_state.get("humanized") or st.session_state.get("balanced") or st.session_state.get("reviewed") or st.session_state.get("draft") or article_area
        if not article or not primary_kw:
            st.warning("الرجاء توفير نص المقال والكلمة المفتاحية.")
        else:
            meta = generate_meta_and_faq(article, primary_kw)
            st.session_state["meta_json"] = json.dumps(meta, ensure_ascii=False, indent=2)
            st.code(st.session_state["meta_json"], language="json")
            if "_warning" in meta:
                st.info(meta["_warning"])
    except Exception as e:
        st.error(f"فشل توليد Meta/FAQ: {e}")

# JSON-LD build
if do_jsonld:
    try:
        if not st.session_state.get("meta_json"):
            st.warning("الرجاء توليد Meta/FAQ أولًا.")
        else:
            from utils.meta_generator import build_jsonld
            meta = json.loads(st.session_state["meta_json"])
            author = {"name": author_name, "credentials": author_credentials}
            reviewer = {"name": reviewed_by}
            article_text = st.session_state.get("humanized") or st.session_state.get("balanced") or st.session_state.get("reviewed") or st.session_state.get("draft") or ""
            schema = build_jsonld(article_text, meta, author, reviewer, last_updated)
            schema_json = json.dumps(schema, ensure_ascii=False, indent=2)
            st.code(schema_json, language="json")
            st.download_button("تحميل JSON-LD", data=schema_json.encode("utf-8"), file_name="article_schema.json", mime="application/ld+json")
    except Exception as e:
        st.error(f"فشل بناء JSON-LD: {e}")

# Balance Rewriter
if do_balance:
    try:
        base_text = st.session_state.get("reviewed") or st.session_state.get("draft") or article_area
        if not base_text or not base_text.strip():
            st.warning("لا يوجد نص لتطبيق إعادة التوازن. الصق نصًا أو ولّد مسودة ثم راجع.")
        else:
            tpl = _read_prompt("balance_rewriter.txt")
            prompt = _format_prompt(tpl, text=base_text)
            balanced = llm(prompt, temperature=0.25, max_tokens=max_tokens).strip()
            st.session_state["balanced"] = balanced
            st.success("تمت إعادة التوازن بين التراث والمعاصر.")
            st.text_area("⚖️ النص بعد إعادة التوازن", value=st.session_state["balanced"], height=400, key="balanced_area")
    except Exception as e:
        st.error(f"فشل تطبيق إعادة التوازن: {e}")

# Human Touch
if do_human:
    try:
        base_text = st.session_state.get("balanced") or st.session_state.get("reviewed") or st.session_state.get("draft") or article_area
        if not base_text or not base_text.strip():
            st.warning("لا يوجد نص لتطبيق اللمسة البشرية. الصق نصًا أو ولّد مسودة ثم راجع.")
        else:
            tpl = _read_prompt("human_touch.txt")
            prompt = _format_prompt(tpl, text=base_text)
            humanized = llm(prompt, temperature=0.3, max_tokens=max_tokens).strip()
            st.session_state["humanized"] = humanized
            st.success("تمت إضافة اللمسة البشرية.")
            st.text_area("👤 النص بعد اللمسة البشرية", value=st.session_state["humanized"], height=400, key="humanized_area")
    except Exception as e:
        st.error(f"فشل تطبيق اللمسة البشرية: {e}")


# Clean sensory/metaphorical language
if do_clean:
    try:
        base = (
            st.session_state.get("humanized")
            or st.session_state.get("balanced")
            or st.session_state.get("reviewed")
            or st.session_state.get("draft")
            or article_area
        )
        if not base or not base.strip():
            st.warning("لا يوجد نص للتنظيف.")
        else:
            cleaned = remove_filler_phrases(base)
            st.session_state["cleaned"] = cleaned.strip()
            st.success("تم تنظيف العبارات الحسية/المجازية.")
            st.text_area("🧽 النص بعد التنظيف", value=st.session_state["cleaned"], height=400, key="cleaned_area")
    except Exception as e:
        st.error(f"فشل التنظيف: {e}")

# Expand "الحالات المؤثرة" to cover missing money scenarios
if do_expand:
    try:
        base = (
            st.session_state.get("cleaned")
            or st.session_state.get("humanized")
            or st.session_state.get("balanced")
            or st.session_state.get("reviewed")
            or st.session_state.get("draft")
            or article_area
        )
        if not base or not base.strip():
            st.warning("لا يوجد نص لتوسيعه.")
        else:
            tpl = _read_prompt("cases_expander.txt")
            prompt = _format_prompt(tpl, article=base)
            expanded = llm(prompt, temperature=0.25, max_tokens=max_tokens).strip()
            st.session_state["expanded"] = expanded
            st.success("تم توسيع قسم الحالات المؤثرة.")
            st.text_area("🧩 النص بعد توسيع الحالات", value=st.session_state["expanded"], height=400, key="expanded_area")
    except Exception as e:
        st.error(f"فشل توسيع الحالات: {e}")

# Export DOCX / PDF (with disclaimer)
if exp_docx or exp_pdf:
    try:
        final_text = st.session_state.get("humanized") or st.session_state.get("balanced") or st.session_state.get("reviewed") or st.session_state.get("draft") or article_area
        if not final_text or not final_text.strip():
            st.warning("لا يوجد نص للتصدير.")
        else:
            final_text = remove_filler_phrases(final_text)
            final_text = ensure_disclaimer(final_text)
            os.makedirs("exports", exist_ok=True)
            if exp_docx:
                docx_path = to_docx(final_text, "exports/article.docx")
                st.download_button("تحميل DOCX", data=_download_bytes(docx_path), file_name="article.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            if exp_pdf:
                pdf_path = to_pdf(final_text, "exports/article.pdf")
                st.download_button("تحميل PDF", data=_download_bytes(pdf_path), file_name="article.pdf", mime="application/pdf")
    except Exception as e:
        st.error(f"فشل التصدير: {e}")

st.caption("© نظام تفسير الأحلام — توليد مسؤول ومتوازن (تراث/علم نفس) | People-first | E-E-A-T")
