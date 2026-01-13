#!/usr/bin/env python3
"""
Quick test with mock background - doesn't call Gemini API.
For testing typography improvements only.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.typography_engine import render_quote_on_image
from modules.utils import ensure_dir
from PIL import Image, ImageDraw
import random

def create_realistic_background(width=1080, height=1080, filename="generated/test_bg.png"):
    """Create a more realistic background with gradients."""
    ensure_dir(filename)
    
    # Create gradient background (top to bottom)
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    
    # Gradient from deep blue to lighter blue
    for y in range(height):
        ratio = y / height
        r = int(25 + (100 * ratio))
        g = int(45 + (150 * ratio))
        b = int(85 + (180 * ratio))
        
        for x in range(width):
            pixels[x, y] = (r, g, b)
    
    # Add some texture/noise
    for _ in range(500):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        curr = pixels[x, y]
        pixels[x, y] = tuple(max(0, min(255, c + random.randint(-20, 20))) for c in curr)
    
    img.save(filename)
    return filename

def test_typography_with_realistic_background():
    """Test typography with better looking mock backgrounds."""
    
    print("\n" + "="*60)
    print(" Testing Typography + Mock Background (NO API CALLS)")
    print("="*60 + "\n")
    
    test_cases = [
        ("powerful", "Push your limits and discover what's truly possible."),
        ("hopeful", "Every challenge is an opportunity to grow stronger."),
    ]
    
    for mood, quote in test_cases:
        print(f"🎨 Generating {mood.upper()} image...")
        
        # Create realistic background
        bg_path = create_realistic_background(filename=f"generated/realistic_bg_{mood}.png")
        
        # Render quote
        output_path = f"generated/final_{mood}.png"
        result = render_quote_on_image(bg_path, quote, mood, output_path)
        
        if os.path.exists(result):
            size = os.path.getsize(result) / 1024
            print(f"   ✅ Success! ({size:.1f} KB)")
            print(f"   Output: {result}\n")
        
        # Cleanup temp background
        if os.path.exists(bg_path):
            os.remove(bg_path)
    
    print("="*60)
    print(" All tests complete! Check 'generated/' folder.")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_typography_with_realistic_background()
