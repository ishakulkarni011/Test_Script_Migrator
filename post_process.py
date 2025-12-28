import re

def strip_code_fences(text: str) -> str:
    fence = re.compile(r"^```(?:python)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)
    return fence.sub("", text).strip()

def ensure_python_file_header(text: str) -> str:
    return text.strip() + "\n"
