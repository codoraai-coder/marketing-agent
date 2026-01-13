import os
import json
import requests
import base64
from typing import Optional
from .utils import ensure_dir, get_env

# --- CONFIGURATION ---
GEMINI_API_KEY = get_env("GEMINI_API_KEY")
STABILITY_API_KEY = get_env("STABILITY_API_KEY", "")  # Optional fallback
# Using Gemini's native image generation (Nano Banana)
MODEL_ID = "gemini-2.5-flash-image"  # Fast, efficient, 1024px resolution
# Alternative: "gemini-3-pro-image-preview"  # Professional, up to 4K, advanced reasoning

def generate_image_with_stability(prompt: str, output_path: str) -> Optional[str]:
    """
    Fallback: Generate image using Stability AI if Gemini fails.
    """
    if not STABILITY_API_KEY:
        return None
    
    try:
        url = "https://api.stability.ai/v1/generate"
        
        payload = {
            "prompt": prompt,
            "negative_prompt": "text, watermark",
            "steps": 30,
            "cfg_scale": 7,
            "width": 1024,
            "height": 1024,
            "samples": 1,
            "sampler": "k_dpmpp_2m"
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {STABILITY_API_KEY}"
        }
        
        print("   Trying Stability AI as fallback...")
        response = requests.post(url, json=payload, headers=headers, timeout=90)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("artifacts"):
                img_data = base64.b64decode(data["artifacts"][0]["base64"])
                with open(output_path, "wb") as f:
                    f.write(img_data)
                print(f"✅ Image generated with Stability AI → {output_path}")
                return output_path
    except Exception as e:
        print(f"   Stability AI fallback failed: {e}")
    
    return None

def generate_image(prompt: str, output_path: str, mode: str = "motivational") -> Optional[str]:
    """
    Generates an image using Google Gemini API (Nano Banana image generation).
    Uses the same GEMINI_API_KEY as text generation for consistency.
    """
    if not GEMINI_API_KEY:
        print("❌ Missing GEMINI_API_KEY in environment variables.")
        return None

    ensure_dir(output_path)

    # 1. Enhance Prompt
    final_prompt = f"{prompt}, photorealistic, cinematic lighting"
    if mode == "motivational":
        final_prompt += ", minimalist, inspiring, soft focus, no text"

    # 2. Prepare Endpoint URL (Gemini API)
    api_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent"

    # 3. Construct Payload for Gemini API
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": final_prompt
                    }
                ]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
    }

    params = {
        "key": GEMINI_API_KEY
    }

    print(f"🎨 Sending request to Gemini API ({MODEL_ID})...")
    print("   ⏳ This may take 30-60 seconds...\n")
    
    try:
        # Reduced timeout to avoid long hangs - Gemini typically responds in 30-60s
        response = requests.post(api_endpoint, headers=headers, json=payload, params=params, timeout=90)
        
        if response.status_code == 200:
            response_json = response.json()
            candidates = response_json.get("candidates", [])
            
            if candidates:
                # Extract image from Gemini response
                parts = candidates[0].get("content", {}).get("parts", [])
                for part in parts:
                    if "inlineData" in part:
                        # Gemini returns base64 encoded image data
                        b64_data = part["inlineData"]["data"]
                        with open(output_path, "wb") as f:
                            f.write(base64.b64decode(b64_data))
                        print(f"✅ Image generated successfully → {output_path}")
                        return output_path
                
                print(f"⚠️ API returned 200 but no image data found in response")
                
        else:
            print(f"❌ Gemini API Error {response.status_code}: {response.text}")
            if response.status_code == 404:
                print("💡 DEBUG: Ensure 'Gemini API' is enabled and GEMINI_API_KEY is valid.")
            if response.status_code == 401:
                print("💡 DEBUG: Check if GEMINI_API_KEY is correct.")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Trying fallback method...")
        fallback_result = generate_image_with_stability(prompt, output_path)
        if fallback_result:
            return fallback_result

    return None
