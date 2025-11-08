from .text_generator import _gemini_call

def generate_hashtags(platform: str, topic: str, caption: str) -> list:
    prompt = (
        f"Generate 10 platform-appropriate hashtags for {platform}. "
        f"Topic: {topic}. Caption: {caption}. Return JSON array of strings."
    )
    out = _gemini_call(prompt)
    try:
        import json
        tags = json.loads(out)
        return [f"#{t.strip().lstrip('#')}" for t in tags][:10]
    except Exception:
        if platform.lower() in {"twitter","x","linkedin"}:
            return ["#"+topic.replace(" ",""), "#Innovation", "#Tech"][:3]
        return ["#"+topic.replace(" ",""), "#Innovation", "#Tech", "#Trends", "#Explained"][:10]
