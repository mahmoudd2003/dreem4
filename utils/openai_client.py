# utils/openai_client.py
# -*- coding: utf-8 -*-
"""
OpenAI client wrapper with a fixed Arabic system prompt tailored for dream interpretation.
Function:
    llm(prompt: str, temperature: float = 0.4, max_tokens: int = 1800) -> str
- Reads OPENAI_API_KEY from .env (python-dotenv).
- Returns text only.
- System prompt enforces: لا حشو، لا تكرار، عبارات حسية باعتدال، تنويه أن التفسير ظني/اجتهادي، موازنة بين التراث والعلم الحديث.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load env once
load_dotenv()

_SYSTEM_PROMPT = (
    "أنت كاتب عربي متخصص في تفسير الأحلام. "
    "التزم بما يلي: "
    "1) لا حشو ولا تكرار أبدًا، "
    "2) أضف عبارات حسّية خفيفة عند الحاجة دون إسراف، "
    "3) وضّح دائمًا أن التفسير ظنّي/اجتهادي وليس قطعيًا، "
    "4) وازن بين التراث (ابن سيرين/النابلسي/ابن شاهين) والعلم الحديث (علم النفس/العقل الباطن) "
    "5) استخدم لغة عربية فصيحة سلسة، جمل متفاوتة الطول، وتجنّب الإنشاء."
)

def llm(prompt: str, temperature: float = 0.4, max_tokens: int = 1800) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY غير موجود. ضع المفتاح في ملف .env")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)

    resp = client.chat.completions.create(
        model=model,
        temperature=float(temperature),
        max_tokens=int(max_tokens),
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    # Return text only
    return (resp.choices[0].message.content or "").strip()
