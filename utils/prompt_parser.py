import re

def parse_prompt(prompt: str):
    text = (prompt or "").strip()
    soc = None
    m = re.search(r'(\d{1,3})\s*%', text)
    if m:
        try:
            v = int(m.group(1))
            if 0 <= v <= 100:
                soc = v
        except: pass
    start = None; dest = None
