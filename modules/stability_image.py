import os
import base64
import requests
from .utils import get_env, ensure_dir

# Load API key
STABILITY_API_KEY = get_env("STABILITY_API_KEY")


def generate_image(prompt: str, output_path: str, mode: str = "motivational") -> str | None:
    """
    Generate an image from text using Stability AI API.
    Falls back automatically between v1 and v2beta endpoints for reliability.
    mode: motivational | cover | architecture
    """

    if not STABILITY_API_KEY:
        print("❌ STABILITY_API_KEY missing in .env")
        return None

    ensure_dir(output_path)

    # Style choice based on mode
    style_preset = {
        "motivational": "enhance",
        "cover": "photographic",
        "architecture": "isometric"
    }.get(mode, "enhance")

    # Compose final prompt
    final_prompt = (
        f"{prompt}. {style_preset} style. Vibrant lighting, realistic atmosphere, "
        f"soft gradients, no text or watermark, cinematic tone."
    )

    print(f"🎨 Generating image (mode={mode})...")
    print(f"🖋️ Prompt: {final_prompt}")

    # --- Primary v1 endpoint ---
    v1_engine = "stable-diffusion-xl-1024-v1-0"
    v1_url = f"https://api.stability.ai/v1/generation/{v1_engine}/text-to-image"

    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "text_prompts": [{"text": final_prompt}],
        "cfg_scale": 8,
        "samples": 1,
        "steps": 35,
        "style_preset": style_preset,
    }

    try:
        response = requests.post(v1_url, headers=headers, json=body, timeout=150)

        # ✅ Success case
        if response.status_code == 200 and "artifacts" in response.json():
            data = response.json()
            if data["artifacts"] and "base64" in data["artifacts"][0]:
                image_base64 = data["artifacts"][0]["base64"]
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(image_base64))
                print(f"✅ Image generated successfully → {output_path}")
                return output_path

        # ❌ If v1 engine not found or empty, fallback to v2beta API
        print("⚠️ v1 engine failed or no artifacts — retrying with v2beta API...")
        return _generate_image_v2beta(final_prompt, output_path, style_preset)

    except Exception as e:
        print(f"❌ Exception in Stability v1 generation: {e}")
        return _generate_image_v2beta(final_prompt, output_path, style_preset)


def _generate_image_v2beta(prompt: str, output_path: str, style_preset: str = "enhance") -> str | None:
    """
    Backup generator using Stability's v2beta /sdxl endpoint.
    Works with free-tier and newer accounts.
    """
    url = "https://api.stability.ai/v2beta/stable-image/generate/"
    headers = {"Authorization": f"Bearer {STABILITY_API_KEY}"}

    files = {
        "prompt": (None, prompt),
        "model": (None, "sdxl"),
        "output_format": (None, "png"),
        "style_preset": (None, style_preset),
        "aspect_ratio": (None, "1:1"),
    }

    try:
        response = requests.post(url, headers=headers, files=files, timeout=180)

        if response.status_code != 200:
            print(f"❌ Stability v2beta error: {response.status_code} → {response.text[:200]}")
            return None

        with open(output_path, "wb") as f:
            f.write(response.content)

        print(f"✅ Image generated successfully via v2beta → {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Exception in v2beta fallback: {e}")
        return None
