# modules/content_builder.py

from .image_builder import generate_final_post_image
from .text_generator import _gemini_call  # use the core Gemini caller directly
from .hashtag_generator import generate_hashtags
from .utils import print_header, get_env

BRAND_VOICE = get_env("BRAND_VOICE", "Insightful, clear, motivational when appropriate. Avoid hype.")

def build_content_from_prompt(prompt: str):
    """
    Step 1: Generate the quote + themed background image with styled typography (motivational mode).
    """
    final_image_path, quote_text = generate_final_post_image(prompt)
    return {
        "topic": prompt,
        "quote_text": quote_text,
        "tone": "motivational"
    }, final_image_path


def _generate_caption_with_gemini(platform: str, topic: str, tone: str = "motivational") -> str:
    """
    Local caption generator using the shared Gemini call.
    Avoids importing a non-existent symbol from text_generator to fix Pylance error.
    """
    prompt = (
        f"You are a top-tier social copywriter.\n"
        f"Platform: {platform}\n"
        f"Topic: {topic}\n"
        f"Tone: {tone}\n"
        f"Brand voice: {BRAND_VOICE}\n\n"
        "Write a short, engaging caption (1–3 lines). No hashtags. "
        "Keep it natural, specific, and human."
    )
    caption = _gemini_call(prompt).strip()
    # Minimal fallback
    if not caption:
        caption = f"{topic} — let's make it happen."
    return caption


def generate_caption_for_platform(platform: str, topic: str, tone: str):
    """
    Step 3: Platform-specific caption (no hashtags).
    """
    print_header(f"Generating Caption for {platform}")
    return _generate_caption_with_gemini(platform, topic, tone)


def generate_platform_hashtags(platform: str, topic: str, caption: str):
    """
    Step 4: Platform-specific hashtags.
    """
    print_header(f"Generating Hashtags for {platform}")
    return generate_hashtags(platform, topic, caption)
