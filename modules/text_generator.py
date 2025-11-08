import json
import requests
from modules.utils import get_env

GEMINI_API_KEY = get_env("GEMINI_API_KEY")
BRAND_VOICE = get_env("BRAND_VOICE", "Insightful, clear, visionary.")
DEFAULT_LANGUAGE = get_env("DEFAULT_LANGUAGE", "en")

def _gemini_call(prompt: str, model: str = "gemini-2.0-flash") -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("❌ GEMINI_API_KEY missing in .env")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    params = {"key": GEMINI_API_KEY}
    try:
        r = requests.post(url, headers=headers, params=params, json=payload, timeout=120)
        if r.status_code != 200:
            print("❌ Gemini error:", r.text); return ""
        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print("❌ Gemini request failed:", e); return ""

# === Motivational ===
def generate_powerful_quote(topic: str) -> str:
    p = ("You are a world-class author. Write a short, ORIGINAL motivational quote about "
         f"'{topic}'. Avoid clichés and author names. Only the quote.")
    t = _gemini_call(p).strip()
    if t.startswith(("\"", "“")) and t.endswith(("\"", "”")) and len(t) > 2: t = t[1:-1].strip()
    return t or f"Keep pushing forward with {topic} in mind."

def generate_caption(platform: str, topic: str, tone: str = "motivational") -> str:
    p = (f"You are a social copywriter.\nPlatform: {platform}\nTopic: {topic}\nTone: {tone}\n"
         f"Brand voice: {BRAND_VOICE}\nWrite 1–3 lines, no hashtags.")
    return _gemini_call(p).strip() or f"{topic} — make it happen."

# === Blog Planning/Writing ===
def plan_blog_outline(topic: str) -> dict:
    p = ("Plan a Medium-style blog outline for the topic below.\n"
         f"Topic: {topic}\nOutput JSON: {{title, sections:[{{heading, summary}}], target_audience, tone}}.")
    out = _gemini_call(p)
    try: return json.loads(out)
    except: 
        return {
            "title": f"Understanding {topic}",
            "sections": [
                {"heading":"Introduction","summary":f"Overview of {topic}."},
                {"heading":"Core Concepts","summary":f"Key ideas in {topic}."},
                {"heading":"Workflow","summary":f"Typical architecture/workflow for {topic}."},
                {"heading":"Use Cases","summary":f"Where {topic} is applied."},
                {"heading":"Challenges","summary":f"Limitations and caveats."},
                {"heading":"Conclusion","summary":"Key takeaways and next steps."},
            ],
            "target_audience":"Developers, PMs, Founders","tone":"informative"
        }

def write_section(heading: str, summary: str, context: str = "", audience: str = "", tone: str = "informative") -> str:
    p = (f"Write a detailed, clear section.\nHeading: {heading}\nGuidance: {summary}\n"
         f"Audience: {audience}\nTone: {tone}\nContext: {context}\n"
         "Use short paragraphs and bullets when helpful.")
    return _gemini_call(p).strip()

# === Visual prompts (context-aware) ===
def suggest_contextual_cover_prompt(topic: str, plan: dict) -> str:
    summaries = "\n".join([f"- {s.get('heading')}: {s.get('summary')}" for s in plan.get("sections", [])])
    p = ("You are a visual concept director for a tech blog.\n"
         f"Topic: {topic}\nBased on these section summaries, describe ONE realistic scene for a cover image. "
         "Avoid abstract words. No text overlays.\n" + summaries)
    return _gemini_call(p).strip()

def validate_mermaid_code(code: str, topic: str) -> str:
    p = ("You are a software architect. Review the Mermaid diagram below for correctness about the topic.\n"
         f"Topic: {topic}\nDiagram:\n{code}\nOutput corrected Mermaid code starting with 'graph'.")
    out = _gemini_call(p).strip()
    return out if out.startswith("graph") else code
