# Use absolute import
from modules.text_generator import plan_blog_outline

def plan(topic: str) -> dict:
    return plan_blog_outline(topic)