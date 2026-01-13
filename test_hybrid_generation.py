#!/usr/bin/env python3
"""
Hybrid Test: Tries real Gemini API, falls back to mock if it times out.
Best of both worlds - real images when available, fast mocks when not.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.google_image import generate_image
from modules.typography_engine import render_quote_on_image
from modules.utils import ensure_dir
from PIL import Image, ImageDraw
import random

def create_mock_background(mood="powerful", filename=None):
    """Create a quick mock background matching the mood."""
    if filename is None:
        filename = f"generated/mock_bg_{mood}.png"
    
    ensure_dir(filename)
    
    # Mood-based color schemes
    mood_colors = {
        "powerful": ((20, 40, 80), (100, 150, 200)),      # Dark to light blue
        "hopeful": ((50, 40, 20), (200, 180, 100)),       # Dark to golden
        "calm": ((40, 60, 80), (150, 180, 220)),          # Soft blues
        "intense": ((60, 30, 20), (200, 100, 80)),        # Dark to orange
    }
    
    start_color, end_color = mood_colors.get(mood, mood_colors["powerful"])
    width, height = 1080, 1080
    
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    
    # Create gradient
    for y in range(height):
        ratio = y / height
        r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
        
        for x in range(width):
            pixels[x, y] = (r, g, b)
    
    # Add subtle texture
    for _ in range(200):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        curr = pixels[x, y]
        pixels[x, y] = tuple(max(0, min(255, c + random.randint(-15, 15))) for c in curr)
    
    img.save(filename)
    return filename

def test_hybrid_generation():
    """Test with real API, fall back to mock if needed."""
    
    print("\n" + "="*70)
    print(" HYBRID TEST: Real AI + Mock Fallback")
    print("="*70 + "\n")
    
    test_cases = [
        ("powerful", "Push beyond your limits and discover infinite potential."),
        ("hopeful", "Every challenge is a stepping stone to greatness."),
    ]
    
    for mood, quote in test_cases:
        print(f"\n🎨 Generating {mood.upper()} image...")
        print(f"   Quote: \"{quote}\"")
        
        ai_bg_path = f"generated/ai_bg_{mood}.png"
        
        # Try real API first
        print("   ⏳ Attempting Gemini API (60s timeout)...")
        ai_result = generate_image(
            f"{quote}, {mood} mood, cinematic, professional",
            ai_bg_path,
            mode="motivational"
        )
        
        # If API works, use it; otherwise use mock
        if ai_result and os.path.exists(ai_result):
            print(f"   ✅ Using AI-generated background")
            bg_path = ai_result
        else:
            print(f"   ⏱️ API timeout - using mock background instead")
            bg_path = create_mock_background(mood)
            print(f"   ✅ Mock background created")
        
        # Render typography
        final_path = f"generated/hybrid_{mood}.png"
        result = render_quote_on_image(bg_path, quote, mood, final_path)
        
        if os.path.exists(result):
            size = os.path.getsize(result) / 1024
            print(f"   ✅ Final image saved: {result} ({size:.1f} KB)\n")
        
        # Cleanup temp AI background if it was created
        if ai_result and os.path.exists(ai_result) and ai_result != bg_path:
            try:
                os.remove(ai_result)
            except:
                pass
    
    print("="*70)
    print(" Hybrid test complete!")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_hybrid_generation()
