import uuid
import os

from modules import text_generator as tg
from modules.image_generator import (
    generate_dynamic_background_prompt,
    analyze_design_mood,
)
from modules.google_image import generate_image, generate_image_with_text
from modules.typography_engine import render_quote_on_image
from modules.utils import print_header


def _safe_generate_quote(topic: str) -> str:
    if hasattr(tg, "generate_powerful_quote") and callable(tg.generate_powerful_quote):
        quote = (tg.generate_powerful_quote(topic) or "").strip()
        if quote:
            return quote

    prompt = (
        f"Write a short, ORIGINAL motivational quote about '{topic}'. "
        f"Return ONLY the quote."
    )
    return (tg._gemini_call(prompt) or "Keep moving forward.").strip('"')


def generate_final_post_image(user_topic: str):
    run_id = uuid.uuid4().hex[:8]

    print_header("Generating Powerful Quote")
    quote = _safe_generate_quote(user_topic)

    print_header("Analyzing Style & Mood")
    mood = analyze_design_mood(quote)

    print_header("Generating Scene Description")
    theme_prompt = generate_dynamic_background_prompt(
        quote, user_topic, mood
    )

    print_header("Creating Image with Embedded Text using Gemini")
    
    final_filename = f"generated/quote_{run_id}.png"
    brand_text = "@aiwithsid | http://grwothbrothers.in"
    
    final_path = generate_image_with_text(
        theme_prompt,
        quote,
        brand_text,
        final_filename,
        mode="motivational",
    )

    if not final_path:
        print("⚠️ Image generation with text failed; returning quote only.")
        return None, quote

    return final_path, quote
