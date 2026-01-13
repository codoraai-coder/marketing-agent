#!/usr/bin/env python3
"""
Quick test script for image generation with new typography improvements.
This bypasses API calls and tests the rendering directly.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.typography_engine import render_quote_on_image
from modules.utils import ensure_dir
from PIL import Image, ImageDraw

def create_test_background(width=1080, height=1080, filename="generated/test_bg.png"):
    """Create a simple test background image for typography testing."""
    ensure_dir(filename)
    
    # Create a gradient-like background
    img = Image.new("RGB", (width, height), color=(25, 45, 85))
    draw = ImageDraw.Draw(img)
    
    # Add some visual interest with a subtle pattern
    for y in range(0, height, 50):
        opacity = int(255 * (y / height) * 0.3)
        color = (100 + opacity // 3, 150 + opacity // 3, 200 + opacity // 3)
        draw.line([(0, y), (width, y)], fill=color)
    
    img.save(filename)
    print(f"✅ Test background created: {filename}")
    return filename

def test_typography_rendering():
    """Test the typography rendering with different moods and quotes."""
    
    test_cases = [
        ("powerful", "Push your limits and discover what's truly possible beyond boundaries."),
        ("calm", "In stillness, we find the clarity to move forward with purpose and grace."),
        ("hopeful", "Every challenge is an opportunity to grow stronger and wiser than before."),
        ("elegant", "Success is not a destination, it's a journey of continuous refinement."),
        ("creative", "Imagination is the bridge between dreams and reality."),
        ("intense", "Become unstoppable by transforming your passion into action."),
    ]
    
    print("\n" + "="*60)
    print(" Testing Typography Rendering with New Text Sizes")
    print("="*60 + "\n")
    
    for mood, quote in test_cases:
        try:
            # Create background for this test
            bg_path = create_test_background(filename=f"generated/test_bg_{mood}.png")
            
            # Render quote with mood styling
            output_path = f"generated/test_quote_{mood}.png"
            final_path = render_quote_on_image(bg_path, quote, mood, output_path)
            
            print(f"✅ [{mood.upper()}] Quote rendered successfully!")
            print(f"   Quote: \"{quote[:50]}...\"")
            print(f"   Output: {final_path}\n")
            
            # Clean up temporary background
            if os.path.exists(bg_path):
                os.remove(bg_path)
                
        except Exception as e:
            print(f"❌ [{mood.upper()}] Error rendering: {e}\n")
    
    print("="*60)
    print(" Test Complete! Check 'generated/' folder for results.")
    print("="*60)

if __name__ == "__main__":
    test_typography_rendering()
