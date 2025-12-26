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
    if hasattr(tg, "generate_powerful_quote") and callable(getattr(tg, "generate_powerful_quote")):
        q = (tg.generate_powerful_quote(topic) or "").strip()
        if q: return q
    prompt = f"Write a short, ORIGINAL motivational quote about '{topic}'. Return ONLY the quote."
    return (tg._gemini_call(prompt) or "Keep moving forward.").strip('"')

def generate_final_post_image(user_topic: str):
    run_id = uuid.uuid4().hex[:8]
    
    print_header("Generating Powerful Quote")
    quote = _safe_generate_quote(user_topic)

    print_header("Analyzing Style & Mood")
    mood = analyze_design_mood(quote)

    print_header("Generating Scene Description")
    theme_prompt = generate_dynamic_background_prompt(quote, user_topic, mood)

    # --- FIXED LOG MESSAGE ---
    print_header("Creating Background with Google Vertex AI")
    bg_filename = f"generated/temp_bg_{run_id}.png"
    
    # Calls the REST API function in google_image.py
    bg_path = generate_image(theme_prompt, bg_filename, mode="motivational")
    
    if not bg_path:
        print("⚠️ Image generation failed; returning quote without image.")
        return None, quote

    print_header("Rendering Typography Overlay")
    final_filename = f"generated/quote_{run_id}.png"
    final_path = render_quote_on_image(bg_path, quote, mood, final_filename)
    
    if os.path.exists(bg_path):
        os.remove(bg_path)

    return final_path, quote
