import os
import requests
import base64
import json
from .utils import get_env, ensure_dir
from typing import Optional

# Reuse the existing Gemini Key
GEMINI_API_KEY = get_env("GEMINI_API_KEY")

def generate_image(prompt: str, output_path: str, mode: str = "motivational") -> Optional[str]:
    """
    Generates an image using Google's 'Nano Banana' (Gemini 2.5 Flash Image) model.
    """
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY missing in .env")
        return None

    ensure_dir(output_path)

    # 1. Enhance prompt for the model
    # Nano Banana works best with direct, photorealistic descriptors
    enhanced_prompt = f"{prompt}. Photorealistic, 8k, cinematic lighting, high detail."
    if mode == "motivational":
        enhanced_prompt += " Inspiring mood, soft glow, minimalist, no text."
    elif mode == "cover":
        enhanced_prompt += " Tech blog cover style, modern, clean."

    print(f"🍌 Generating image with Nano Banana (Gemini)...")
    
    # 2. Call the API
    # Using the Gemini 2.5 Flash Image endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": enhanced_prompt}]
        }],
        "generationConfig": {
            "mimeType": "image/png",
            "candidateCount": 1
        }
    }

    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            # Extract Base64 image
            try:
                img_data = data["candidates"][0]["content"]["parts"][0]["inline_data"]["data"]
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(img_data))
                print(f"✅ Image generated successfully → {output_path}")
                return output_path
            except KeyError:
                print(f"⚠️ Unexpected response structure: {data}")
        else:
            print(f"⚠️ Generation error {response.status_code}: {response.text}")
            # Optional: Fallback to Imagen 3 if Nano Banana is experimental/busy
            return _generate_imagen_fallback(enhanced_prompt, output_path)

    except Exception as e:
        print(f"❌ Image generation failed: {e}")
    
    return None

def _generate_imagen_fallback(prompt: str, output_path: str) -> Optional[str]:
    """Fallback to Imagen 3 if Gemini 2.5 is unavailable."""
    print("⚠️ Falling back to Imagen 3...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={GEMINI_API_KEY}"
    payload = {"instances": [{"prompt": prompt}], "parameters": {"sampleCount": 1}}
    
    try:
        r = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        if r.status_code == 200:
            data = r.json()
            img_data = data["predictions"][0]["bytesBase64Encoded"]
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(img_data))
            print(f"✅ Image generated (Imagen 3) → {output_path}")
            return output_path
        else:
            print(f"❌ Imagen 3 fallback failed: {r.text}")
    except Exception as e:
        print(f"❌ Imagen 3 error: {e}")
    return None