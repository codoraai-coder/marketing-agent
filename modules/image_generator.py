# modules/image_generator.py

from modules.text_generator import _gemini_call
from modules.google_image import generate_image # Make sure you have this import if needed elsewhere

_VALID_MOODS = {"calm", "hopeful", "powerful", "creative", "elegant", "intense"}

def analyze_design_mood(quote_text: str) -> str:
    """
    Return one of: calm, hopeful, powerful, creative, elegant, intense. Fallback to 'powerful'.
    """
    prompt = (
        "Classify the emotional tone of this quote as ONE word from "
        "calm, hopeful, powerful, creative, elegant, intense.\n"
        f"Quote: \"{quote_text}\"\n"
        "Return only the word."
    )
    mood = (_gemini_call(prompt) or "").strip().lower()
    return mood if mood in _VALID_MOODS else "powerful"


def _extract_visual_subject(quote_text: str, topic: str) -> str:
    """
    Produce ONE concrete visual subject tied to the quote/topic (no abstractions).
    """
    prompt = (
        "You are an art director. Propose ONE concrete visual subject (not abstract) that represents this quote/topic.\n"
        f"Quote: \"{quote_text}\"\nTopic: {topic}\n"
        "Examples: 'mountain climber at sunrise', 'runner in rain', 'phoenix rising'.\n"
        "Return <= 12 words, no extra text."
    )
    subject = (_gemini_call(prompt) or "").strip().strip('"')
    return subject or "sunrise over mountains"


def generate_dynamic_background_prompt(quote_text: str, topic: str, mood: str) -> str:
    """
    Build a concise, content-aware Stability prompt: subject + mood + environment hints.
    """
    subject = _extract_visual_subject(quote_text, topic)
    prompt = (
        "Create a vivid background scene description for a motivational poster image.\n"
        f"Subject: {subject}\nMood: {mood}\nTopic: {topic}\n"
        "Add realistic environment/lighting (e.g., golden sunrise, soft fog, dramatic clouds). "
        "Avoid any text/typography. One concise line."
    )
    scene = (_gemini_call(prompt) or "").strip()
    return scene or f"{subject}, cinematic lighting, {mood} atmosphere, no text"


def generate_section_image(topic: str, description: str, context: str, output_path: str) -> str | None:
    """
    Generates an image for a blog section based on a detailed prompt.
    This function acts as a wrapper around the core image generation logic.
    """
    print(f"🖼️  Generating section image for '{description}'...")
    
    # Create a detailed prompt for the image generation service
    prompt = (
        f"Create a high-quality, realistic image for a blog post about '{topic}'. "
        f"The image should visually represent: '{description}'. "
        f"Use the following context for inspiration: {context}. "
        "The style should be photographic and cinematic, suitable for a tech blog. Avoid text or watermarks."
    )
    
    # Call the actual image generation function from stability_image.py
    # We'll use the "cover" mode for a photographic style.
    image_path = generate_image(prompt, output_path, mode="cover")
    
    if not image_path:
        print(f"⚠️  Failed to generate section image for: {description}")
        return None
        
    return image_path