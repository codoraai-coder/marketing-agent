#!/usr/bin/env python3
"""
Test the Gemini API image generation (Nano Banana).
This tests the new google_image.py implementation.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.google_image import generate_image
from modules.utils import print_header

def test_gemini_image_generation():
    """Test image generation using Gemini API."""
    
    print_header("Testing Gemini API Image Generation")
    
    test_prompts = [
        "A serene sunrise over mountains with golden light, minimalist, inspiring",
        "Professional workspace with modern design and good lighting",
        "Abstract geometric patterns with vibrant colors and smooth gradients",
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n🎨 Test {i}/3: Generating image...")
        print(f"   Prompt: {prompt[:60]}...")
        
        output_path = f"generated/gemini_test_{i}.png"
        
        try:
            result = generate_image(prompt, output_path, mode="motivational")
            
            if result and os.path.exists(result):
                file_size = os.path.getsize(result) / 1024  # KB
                print(f"   ✅ Success! ({file_size:.1f} KB)")
            else:
                print(f"   ❌ Failed - file not created")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "="*60)
    print(" Gemini API Test Complete!")
    print("="*60)

if __name__ == "__main__":
    test_gemini_image_generation()
