import os
import requests
import base64
import json
from .utils import get_env, ensure_dir
from typing import Optional

# Reuse the existing Gemini Key
GEMINI_API_KEY = get_env("GEMINI_API_KEY")

# The specific model you requested
MODEL_NAME = "image-generation-001"

def generate_image(prompt: str, output_path: str, mode: str = "motivational") -> Optional[str]:
    """
    Generates an image using the specific 'gemini-2.5-flash-image' model.
    """
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY missing in .env")
        return None

    ensure_dir(output_path)

    # 1. Prepare Prompt
    # Gemini models often perform better with a clear instruction wrapper
    enhanced_prompt = f"Generate a photorealistic image: {prompt}"
    if mode == "motivational":
        enhanced_prompt += ". Style: Cinematic, inspiring, minimalist, no text."
    
    print(f"🍌 Generating image with {MODEL_NAME}...")
    
    # 2. API Endpoint
    # Using the standard Gemini :generateContent method
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": enhanced_prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "image/png"  # Requesting image output explicitly
        }
    }

    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
        
        # 3. Handle Response
        if response.status_code == 200:
            data = response.json()
            
            # Check for inline image data (standard Gemini image output format)
            try:
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    for part in parts:
                        if "inline_data" in part:
                            # Found the image!
                            b64_data = part["inline_data"]["data"]
                            with open(output_path, "wb") as f:
                                f.write(base64.b64decode(b64_data))
                            print(f"✅ Image generated successfully → {output_path}")
                            return output_path
                        
                print(f"⚠️ API returned 200 but no inline_data found. Response: {json.dumps(data)[:200]}...")

            except Exception as parse_error:
                print(f"❌ Error parsing success response: {parse_error}")
                print(f"Full Response: {data}")
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")
            
            # Help debug 404s specifically
            if response.status_code == 404:
                print(f"💡 DEBUG: The model '{MODEL_NAME}' was not found.")
                print("   Run 'curl https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_KEY' to list available models.")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
    
    return None
