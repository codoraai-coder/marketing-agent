import os
import base64
import requests
from typing import Optional

from .utils import ensure_dir, get_env

# --- CONFIGURATION ---
GEMINI_API_KEY = get_env("GEMINI_API_KEY")
STABILITY_API_KEY = get_env("STABILITY_API_KEY", "")  # optional fallback

MODEL_ID = "gemini-2.5-flash-image"
GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"models/{MODEL_ID}:generateContent"
)


def generate_image_with_stability(prompt: str, output_path: str) -> Optional[str]:
    """
    Fallback image generation using Stability AI.
    """
    if not STABILITY_API_KEY:
        return None

    try:
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

        payload = {
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 7,
            "steps": 30,
            "height": 1024,
            "width": 1024,
            "samples": 1,
        }

        headers = {
            "Authorization": f"Bearer {STABILITY_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        print("🔁 Gemini failed — trying Stability AI fallback...")
        res = requests.post(url, json=payload, headers=headers, timeout=90)

        if res.status_code == 200:
            img_b64 = res.json()["artifacts"][0]["base64"]
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(img_b64))
            print(f"✅ Image generated via Stability → {output_path}")
            return output_path

    except Exception as e:
        print(f"❌ Stability fallback failed: {e}")

    return None


def generate_image_with_text(
    prompt: str,
    quote_text: str,
    brand_text: str,
    output_path: str,
    mode: str = "motivational",
) -> Optional[str]:
    """
    Generate image with quote text embedded using Gemini Image API.
    """

    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY missing in environment.")
        return None

    ensure_dir(output_path)

    # Enhanced prompt with text specifications
    final_prompt = f"""{prompt}, photorealistic, cinematic lighting.
    
The image MUST include the following text elements:
    
    1. Main Quote (large, centered, highly readable): "{quote_text}"
       - Use large, bold, white text with strong black outline/shadow
       - Center the text prominently on the image
       - Text should have maximum contrast for readability
    
    2. Branding (bottom-left corner, small): "{brand_text}"
       - Small white text with shadow
       - Positioned in bottom-left corner
    
    Text should be clearly legible, professional, and well-integrated into the design.
    """
    
    if mode == "motivational":
        final_prompt += "\nMinimalist, inspiring aesthetic, professional typography."

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

    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}

    print(f"🎨 Generating image with embedded text using {MODEL_ID}...")

    try:
        response = requests.post(
            GEMINI_ENDPOINT,
            headers=headers,
            json=payload,
            params=params,
            timeout=90,
        )

        if response.status_code != 200:
            print(f"❌ Gemini API error {response.status_code}: {response.text}")
            return None

        data = response.json()
        candidates = data.get("candidates", [])

        if not candidates:
            print("⚠️ Gemini returned no candidates.")
            return None

        for part in candidates[0]["content"]["parts"]:
            if "inlineData" in part:
                img_b64 = part["inlineData"]["data"]
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(img_b64))
                print(f"✅ Image with embedded text generated → {output_path}")
                return output_path

        print("⚠️ No image data found in Gemini response.")
        return None

    except Exception as e:
        print(f"❌ Gemini request failed: {e}")
        return None


def generate_image(
    prompt: str,
    output_path: str,
    mode: str = "motivational",
) -> Optional[str]:
    """
    Generate image using Gemini Image API (Nano Banana).
    """

    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY missing in environment.")
        return None

    ensure_dir(output_path)

    final_prompt = f"{prompt}, photorealistic, cinematic lighting"
    if mode == "motivational":
        final_prompt += ", minimalist, inspiring, soft focus, no text"

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

    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}

    print(f"🎨 Generating image using {MODEL_ID}...")

    try:
        response = requests.post(
            GEMINI_ENDPOINT,
            headers=headers,
            json=payload,
            params=params,
            timeout=90,
        )

        if response.status_code != 200:
            print(f"❌ Gemini API error {response.status_code}: {response.text}")
            return generate_image_with_stability(prompt, output_path)

        data = response.json()
        candidates = data.get("candidates", [])

        if not candidates:
            print("⚠️ Gemini returned no candidates.")
            return generate_image_with_stability(prompt, output_path)

        for part in candidates[0]["content"]["parts"]:
            if "inlineData" in part:
                img_b64 = part["inlineData"]["data"]
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(img_b64))
                print(f"✅ Image generated → {output_path}")
                return output_path

        print("⚠️ No image data found in Gemini response.")
        return generate_image_with_stability(prompt, output_path)

    except Exception as e:
        print(f"❌ Gemini request failed: {e}")
        return generate_image_with_stability(prompt, output_path)
