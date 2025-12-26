import os
import requests
import base64
from .utils import get_env, ensure_dir
from typing import Optional

GEMINI_API_KEY = get_env("GEMINI_API_KEY")

def generate_image(prompt: str, output_path: str, mode: str = "motivational") -> Optional[str]:
    """
    Robust Google Image Generator.
    Tries 'Imagen 3' first. If unavailable, falls back to 'Imagen 2'.
    """
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY missing.")
        return None

    ensure_dir(output_path)
    
    # Enhancing the prompt for better results
    full_prompt = f"{prompt}. Photorealistic, 8k, cinematic lighting."
    if mode == "motivational":
        full_prompt += " Minimalist, inspiring, no text, soft focus."

    # 1. Try Imagen 3 (Newest, Best Quality)
    print(f"🎨 Generating image... trying 'imagen-3.0-generate-001'...")
    if _try_generate_via_predict(full_prompt, output_path, "imagen-3.0-generate-001"):
        return output_path

    # 2. Fallback to Imagen 2 (Standard Availability)
    print(f"⚠️ Imagen 3 not found. Falling back to 'image-generation-001'...")
    if _try_generate_via_predict(full_prompt, output_path, "image-generation-001"):
        return output_path

    print("❌ All Google Image models failed. Check your API Key permissions.")
    return None

def _try_generate_via_predict(prompt: str, output_path: str, model_id: str) -> bool:
    """
    Helper to call the correct 'predict' endpoint for image models.
    """
    # CRITICAL: Image models use ':predict', NOT ':generateContent'
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:predict?key={GEMINI_API_KEY}"
    
    payload = {
        "instances": [
            {
                "prompt": prompt
            }
        ],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "1:1"
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=55)
        
        if response.status_code == 200:
            data = response.json()
            if "predictions" in data and data["predictions"]:
                # Success! Decode and save.
                b64_data = data["predictions"][0]["bytesBase64Encoded"]
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(b64_data))
                print(f"✅ Image generated successfully ({model_id}) → {output_path}")
                return True
            else:
                print(f"⚠️ {model_id} returned 200 but no image data.")
        elif response.status_code == 404:
            print(f"⚠️ Model {model_id} not available (404).")
        else:
            print(f"❌ {model_id} Error {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Exception calling {model_id}: {e}")
        
    return False
