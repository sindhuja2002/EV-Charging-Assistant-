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



    model = None
    known = ['Tesla Model 3','Tesla Model Y','Nissan Leaf','Hyundai Kona','BMW i4']
    for name in known:
        if name.lower() in text.lower():
            model = name; break
        

        
    if not model:
        m3 = re.search(r'car\s+([A-Za-z0-9 ]{3,40})', text, flags=re.IGNORECASE)
        if m3: model = m3.group(1).strip(' ,.;')
    return {"start": start, "dest": dest, "soc": soc, "model": model}