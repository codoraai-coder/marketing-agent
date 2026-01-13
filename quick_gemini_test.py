#!/usr/bin/env python3
"""
Quick test of Gemini API image generation - with text overlay.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.google_image import generate_image
from modules.typography_engine import render_quote_on_image

print("\n🎨 Testing Gemini API Image Generation (Nano Banana)...\n")

prompt = "A minimalist sunrise over mountains with golden light, cinematic"
bg_path = "generated/gemini_test_bg.png"
output_path = "generated/gemini_test_final.png"
quote = "Push your limits and discover what's truly possible."

print(f"📝 Quote: \"{quote}\"")
print(f"📸 Prompt: {prompt}\n")
print("⏳ Step 1/2: Generating background (30-60 seconds)...\n")

# Step 1: Generate background
result = generate_image(prompt, bg_path, mode="motivational")

if result and os.path.exists(result):
    file_size = os.path.getsize(result) / 1024
    print(f"✅ Background generated: {file_size:.1f} KB\n")
    
    # Step 2: Overlay text
    print("⏳ Step 2/2: Overlaying quote text...\n")
    final = render_quote_on_image(result, quote, "powerful", output_path)
    
    if os.path.exists(final):
        final_size = os.path.getsize(final) / 1024
        print(f"✅ Final image with text: {final_size:.1f} KB")
        print(f"📍 Saved to: {final}\n")
    
    # Cleanup
    try:
        os.remove(result)
    except:
        pass
else:
    print(f"❌ Failed to generate background\n")
