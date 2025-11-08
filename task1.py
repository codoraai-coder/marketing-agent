import os
import json
import enum
import argparse
import random
import base64
from typing import Optional, List, Dict, Any
import requests
from dotenv import load_dotenv
load_dotenv()

# =========================
# CONFIG
# =========================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
BRAND_VOICE = os.getenv("BRAND_VOICE", "Friendly, motivational, and authentic. Use emojis sparingly.")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")

# =========================
# ENUMS
# =========================

class Platform(str, enum.Enum):
    twitter = "twitter"
    linkedin = "linkedin"
    instagram = "instagram"
    facebook = "facebook"
    threads = "threads"
    auto = "auto"

class ContentType(str, enum.Enum):
    professional_post = "professional_post"
    casual_post = "casual_post"
    meme = "meme"
    carousel = "carousel"
    infographic = "infographic"
    announcement = "announcement"
    promo = "promo"
    news_recap = "news_recap"

class MediaDecision(str, enum.Enum):
    none = "none"
    generate_image = "generate_image"

# =========================
# DATA CLASSES
# =========================

class Intent:
    def __init__(self, platform, content_type, topic, tone, language, hashtags_needed, include_emojis):
        self.platform = platform
        self.content_type = content_type
        self.topic = topic
        self.tone = tone
        self.language = language
        self.hashtags_needed = hashtags_needed
        self.include_emojis = include_emojis

class MediaPlan:
    def __init__(self, decision, reason, style_prompt=None):
        self.decision = decision
        self.reason = reason
        self.style_prompt = style_prompt

class PostDraft:
    def __init__(self, caption, hashtags, platform_notes, media):
        self.caption = caption
        self.hashtags = hashtags
        self.platform_notes = platform_notes
        self.media = media

class FinalPost:
    def __init__(self, platform, content_type, text, hashtags, media_urls, media_generation_details):
        self.platform = platform
        self.content_type = content_type
        self.text = text
        self.hashtags = hashtags
        self.media_urls = media_urls
        self.media_generation_details = media_generation_details

# =========================
# GEMINI (TEXT)
# =========================

def gemini_generate_text(prompt: str, model: str = "gemini-2.0-flash") -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("❌ GEMINI_API_KEY missing in .env file.")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    params = {"key": GEMINI_API_KEY}

    resp = requests.post(url, headers=headers, params=params, json=payload)
    if resp.status_code != 200:
        raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text}")
    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return json.dumps(data)

# =========================
# STABILITY (IMAGE)
# =========================

def generate_image_stability(style_prompt: str, save_path: str = "generated_image.png") -> Optional[str]:
    """
    Generates an image using Stability AI and saves it locally.
    Returns file path if successful.
    """
    if not STABILITY_API_KEY:
        print("⚠️ No STABILITY_API_KEY found. Skipping image generation.")
        return None

    try:
        print(f"🎨 Generating image with Stability AI for prompt: {style_prompt}")
        resp = requests.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image",
            headers={"Authorization": f"Bearer {STABILITY_API_KEY}"},
            json={
                "text_prompts": [{"text": style_prompt}],
                "cfg_scale": 8,
                "clip_guidance_preset": "FAST_BLUE",
                "samples": 1,
                "steps": 30,
            },
        )
        if resp.status_code == 200:
            data = resp.json()
            if "artifacts" in data and len(data["artifacts"]) > 0:
                image_base64 = data["artifacts"][0]["base64"]
                image_bytes = base64.b64decode(image_base64)
                with open(save_path, "wb") as f:
                    f.write(image_bytes)
                print(f"✅ Image saved as: {save_path}")
                return save_path
            else:
                print("⚠️ No image returned by Stability API.")
        else:
            print("❌ Stability API error:", resp.text)
    except Exception as e:
        print("❌ Exception during Stability image generation:", e)
    return None

# =========================
# CORE PIPELINE
# =========================

def classify_intent(user_prompt: str) -> Intent:
    prompt = (
        f"Classify this prompt for social media post generation.\n"
        f"Return JSON with keys: platform, content_type, topic, tone, language, hashtags_needed, include_emojis.\n"
        f"Prompt: {user_prompt}"
    )
    out = gemini_generate_text(prompt)
    try:
        parsed = json.loads(out)
    except Exception:
        parsed = {
            "platform": "auto",
            "content_type": "casual_post",
            "topic": user_prompt,
            "tone": "motivational",
            "language": DEFAULT_LANGUAGE,
            "hashtags_needed": True,
            "include_emojis": True,
        }

    return Intent(
        platform=Platform(parsed.get("platform", "auto")),
        content_type=ContentType(parsed.get("content_type", "casual_post")),
        topic=parsed.get("topic", user_prompt),
        tone=parsed.get("tone", "motivational"),
        language=parsed.get("language", DEFAULT_LANGUAGE),
        hashtags_needed=parsed.get("hashtags_needed", True),
        include_emojis=parsed.get("include_emojis", True),
    )

def generate_caption(intent: Intent) -> PostDraft:
    prompt = (
        f"You are a social media copywriter. Brand voice: {BRAND_VOICE}. "
        f"Write a {intent.content_type} for {intent.platform}. "
        f"Topic: {intent.topic}. Tone: {intent.tone}. Language: {intent.language}. "
        f"Include emojis: {intent.include_emojis}. Hashtags needed: {intent.hashtags_needed}. "
        "Output JSON with keys: caption, hashtags (list), platform_notes."
    )
    out = gemini_generate_text(prompt)
    try:
        data = json.loads(out)
    except Exception:
        data = {"caption": out, "hashtags": [], "platform_notes": ""}

    caption = data.get("caption", out)
    hashtags = data.get("hashtags", [])
    notes = data.get("platform_notes", "")
    media_plan = decide_media(intent, caption)
    return PostDraft(caption, hashtags, notes, media_plan)

def decide_media(intent: Intent, caption: str) -> MediaPlan:
    if intent.content_type in [ContentType.meme, ContentType.infographic] or \
       intent.platform in [Platform.instagram, Platform.threads]:
        return MediaPlan(MediaDecision.generate_image, "Visual platform - motivational style", caption)
    return MediaPlan(MediaDecision.none, "Text-only post is fine")

def materialize_media(media: MediaPlan):
    """
    Generates motivational quote image with Stability AI.
    """
    urls, details = [], {}

    if media.decision == MediaDecision.generate_image:
        quote_text = media.style_prompt or "Keep pushing forward."
        style_prompt = (
            f"Create a minimalist motivational quote poster. "
            f"Include this text prominently: '{quote_text}'. "
            f"Design style: clean typography, neutral background, soft lighting, "
            f"a small plant or workspace element, realistic photo style. "
            f"Suitable for Instagram inspiration posts. Resolution 1024x1024."
        )

        image_path = generate_image_stability(style_prompt)
        if image_path:
            urls.append(image_path)
            details = {"provider": "stability", "style_prompt": style_prompt}

    return urls, (details if details else None)

def platform_auto_detect(intent: Intent, user_prompt: str) -> Platform:
    if intent.platform != Platform.auto:
        return intent.platform
    text = user_prompt.lower()
    if "linkedin" in text or "b2b" in text:
        return Platform.linkedin
    if "instagram" in text or "meme" in text:
        return Platform.instagram
    if "tweet" in text or "x.com" in text:
        return Platform.twitter
    return random.choice([Platform.instagram, Platform.linkedin, Platform.twitter])

def build_final_post(prompt: str) -> FinalPost:
    intent = classify_intent(prompt)
    platform = platform_auto_detect(intent, prompt)
    intent.platform = platform
    draft = generate_caption(intent)
    media_urls, media_details = materialize_media(draft.media)

    text = draft.caption
    if draft.hashtags:
        text += "\n\n" + " ".join([f"#{h}" for h in draft.hashtags])

    return FinalPost(platform, intent.content_type, text, draft.hashtags, media_urls, media_details)

# =========================
# CLI ENTRY
# =========================

def main():
    parser = argparse.ArgumentParser(description="AI Social Post Generator (Gemini + Stability)")
    parser.add_argument("--prompt", help="User prompt for the post")
    args = parser.parse_args()

    if not args.prompt:
        args.prompt = input("Enter your post prompt: ")

    post = build_final_post(args.prompt)

    print("\n=== FINAL POST ===")
    print(f"Platform: {post.platform}")
    print(f"Content Type: {post.content_type}")
    print("\n" + post.text)
    if post.media_urls:
        print("\n🖼️ Generated Image(s):")
        for u in post.media_urls:
            print("-", u)
    if post.media_generation_details:
        print("\nMedia Details:", json.dumps(post.media_generation_details, indent=2))

if __name__ == "__main__":
    main()
