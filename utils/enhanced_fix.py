# utils/enhanced_fix.py
# -*- coding: utf-8 -*-
DISCLAIMER = (
    "تنويه: التفسير اجتهادي وقد يختلف من شخص لآخر. عند القلق المستمر أو ظهور أعراض مؤثرة "
    "على الصحة النفسية، يُستحسن مراجعة مختص."
)
def ensure_disclaimer(text: str) -> str:
    t = text or ""
    if "تنويه" in t and "اجتهادي" in t:
        return t
    sep = "\n\n" if not t.endswith("\n") else "\n"
    return t + sep + DISCLAIMER + "\n"
