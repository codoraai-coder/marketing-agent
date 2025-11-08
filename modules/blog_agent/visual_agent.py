# modules/blog_agent/visual_agent.py
import json
import re
from modules.text_generator import _gemini_call

def decide_visuals_for_section(heading: str, content: str) -> list[dict]:
    """
    Asks Gemini for the CORE KEYWORDS for a potential visual.
    This prompt is optimized for the new Query Cascade retrieval system.
    """
    prompt = (
        "You are a technical editor. Your task is to suggest visuals for the section below.\n"
        "Return ONLY a JSON array. Each object must have:\n"
        "- \"type\": 'diagram' or 'image'.\n"
        "- \"keywords\": A JSON list of 2-3 essential keywords (e.g., [\"RNN architecture\", \"speech recognition\"]). DO NOT use a single string or long sentences.\n"
        "- \"after_paragraph\": 0-based index for insertion.\n\n"
        f"## Section to Analyze:\n"
        f"### Heading: {heading}\n"
        f"### Content:\n{content}\n"
    )
    
    for _ in range(2): 
        out = _gemini_call(prompt).strip()
        
        json_match = re.search(r'\[\s*\{.*?\}\s*\]', out, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                arr = json.loads(json_str)
                cleaned = []
                for v in arr if isinstance(arr, list) else []:
                    t = (v.get("type") or "").lower()
                    
                    # Correctly handle the list of keywords and join them into a string
                    keywords_val = v.get("keywords")
                    if isinstance(keywords_val, list):
                        keywords = " ".join(keywords_val)
                    elif isinstance(keywords_val, str):
                        keywords = keywords_val # Fallback if AI messes up
                    else:
                        continue

                    if t in {"diagram", "image"} and keywords.strip():
                        idx = v.get("after_paragraph", 0)
                        cleaned.append({"type": t, "keywords": keywords.strip(), "after_paragraph": idx})
                
                if cleaned:
                    print(f"✅ Visual agent identified keywords for {len(cleaned)} visuals in section '{heading}'.")
                    return cleaned[:2]
            except json.JSONDecodeError:
                continue
    
    print(f"❌ Visual agent failed to generate keywords for section '{heading}'.")
    return []