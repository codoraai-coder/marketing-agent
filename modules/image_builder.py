# modules/image_builder.py

import uuid
import os
from modules import text_generator as tg
from modules.image_generator import (
    generate_dynamic_background_prompt,
    analyze_design_mood,
)
from modules.google_image import generate_image
from modules.typography_engine import render_quote_on_image
from modules.utils import print_header

def _safe_generate_quote(topic: str) -> str:
    """
    Prefer tg.generate_powerful_quote; fall back to direct Gemini call if needed.
    """
    if hasattr(tg, "generate_powerful_quote") and callable(getattr(tg, "generate_powerful_quote")):
        q = (tg.generate_powerful_quote(topic) or "").strip()
        if q:
            return q

    # Fallback
    prompt = (
        "You are a world-class author. Write a short, ORIGINAL motivational quote about "
        f"'{topic}'. Avoid clichés and author names. Return ONLY the quote text."
    )
    if hasattr(tg, "_gemini_call"):
        q = (tg._gemini_call(prompt) or "").strip()
        if q.startswith(("\"", "“")) and q.endswith(("\"", "”")) and len(q) > 2:
            q = q[1:-1].strip()
        return q or f"Keep moving forward with {topic} in mind."
    return f"Keep moving forward with {topic} in mind."

def generate_final_post_image(user_topic: str):
    """
    Motivational poster pipeline with UNIQUE filenames.
    """
    # Generate a unique ID for this request (first 8 chars is enough entropy for this)
    run_id = uuid.uuid4().hex[:8]
    
    print_header("Generating Powerful Quote")
    quote = _safe_generate_quote(user_topic)

    print_header("Analyzing Style & Mood")
    mood = analyze_design_mood(quote)

    print_header("Generating Scene Description")
    theme_prompt = generate_dynamic_background_prompt(quote, user_topic, mood)

    print_header("Creating Background with Stability AI")
    # Use unique filename for the background
    bg_filename = f"generated/temp_bg_{run_id}.png"
    bg_path = generate_image(theme_prompt, bg_filename, mode="motivational")
    
    if not bg_path:
        print("⚠️ Background generation failed; returning quote without image.")
        return None, quote

    print_header("Rendering Typography Overlay")
    # Use unique filename for the final output
    final_filename = f"generated/quote_{run_id}.png"
    final_path = render_quote_on_image(bg_path, quote, mood, final_filename)
    
    # Optional: Clean up the temp background to save space
    try:
        if os.path.exists(bg_path):
            os.remove(bg_path)
    except Exception:
        pass

    return final_path, quote