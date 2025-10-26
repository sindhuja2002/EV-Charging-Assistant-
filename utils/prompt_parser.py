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


    m = re.search(r'\bfrom\s+(.+?)\s+to\s+(.+)', text, flags=re.IGNORECASE)
    if m:
        start = m.group(1).strip(' ,.;'); dest = m.group(2).strip(' ,.;')



    if not (start and dest):
        m2 = re.search(r'(.+?)\s+to\s+(.+)', text, flags=re.IGNORECASE)
        if m2:
            start = start or m2.group(1).strip(' ,.;')
            dest = dest or m2.group(2).strip(' ,.;')


