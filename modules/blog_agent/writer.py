# modules/blog_agent/writer.py
from modules.text_generator import write_section

def write_sections(plan: dict, topic: str) -> list[tuple[str, str]]:
    """
    Returns list of (heading, content) for each section.
    plan: {title, sections: [{heading, summary}], target_audience, tone}
    """
    audience = plan.get("target_audience", "")
    tone = plan.get("tone", "informative")
    results = []
    for sec in plan.get("sections", []):
        heading = sec.get("heading", "Section")
        summary = sec.get("summary", "")
        content = write_section(heading, summary, audience=audience, tone=tone)
        results.append((heading, content))
    return results
