import os
from textwrap import wrap
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from .utils import ensure_dir, image_luminance

# --- Define Project Root to find assets/logo.jpg ---
# This makes the path robust, finding D:\Marketing Agent\assets\logo.jpg
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
LOGO_PATH = os.path.join(PROJECT_ROOT, "assets", "logo.jpg")

# Font paths
FONT_PATHS = {
    "serif": "times.ttf",
    "sans": "arial.ttf",
    "display": "impact.ttf",
    "hand": "comic.ttf",
}

# Visual presets
MOOD_STYLES = {
    "calm": {
        "font_family": "serif", "color": (220, 230, 255), "base_size": 72,
        "italic": True, "bold": False, "y_offset": 0.15,
    },
    "hopeful": {
        "font_family": "sans", "color": (255, 235, 180), "base_size": 84,
        "italic": False, "bold": True, "y_offset": 0.0,
    },
    "powerful": {
        "font_family": "display", "color": (255, 255, 255), "base_size": 96,
        "italic": False, "bold": True, "y_offset": 0.0,
    },
    "creative": {
        "font_family": "hand", "color": (255, 240, 230), "base_size": 78,
        "italic": True, "bold": False, "y_offset": -0.1,
    },
    "elegant": {
        "font_family": "serif", "color": (255, 250, 240), "base_size": 80,
        "italic": True, "bold": False, "y_offset": 0.1,
    },
    "intense": {
        "font_family": "display", "color": (255, 200, 180), "base_size": 90,
        "italic": False, "bold": True, "y_offset": -0.1,
    },
    "neutral": {
        "font_family": "sans", "color": (255, 255, 255), "base_size": 78,
        "italic": False, "bold": False, "y_offset": 0.0,
    },
}

def _load_font(family: str, size: int):
    font_path = FONT_PATHS.get(family, "arial.ttf")
    try:
        return ImageFont.truetype(font_path, size)
    except:
        return ImageFont.load_default()

def _auto_color_for_background(img, preferred_rgb):
    lum = image_luminance(img)
    if lum > 150: return (20, 20, 40)
    elif lum < 80: return (255, 255, 255)
    return preferred_rgb

def _apply_fake_style(draw, x, y, text, font, color, bold, italic, align, spacing=8):
    if italic:
        offset = 2
        for i, line in enumerate(text.split("\n")):
            draw.text((x + offset, y + i * (font.size + spacing)), line, font=font, fill=color, align=align)
            offset += 1
    elif bold:
        for dx, dy in [(0, 0), (1, 0), (0, 1), (1, 1)]:
            draw.multiline_text((x + dx, y + dy), text, font=font, fill=color, align=align, spacing=spacing)
    else:
        draw.multiline_text((x, y), text, font=font, fill=color, align=align, spacing=spacing)

def render_quote_on_image(background_path: str, quote_text: str, mood: str, output_path: str = "generated/final_quote_image.png"):
    from random import randint
    style = MOOD_STYLES.get(mood, MOOD_STYLES["neutral"])
    ensure_dir(output_path)

    img = Image.open(background_path).convert("RGBA")
    img = ImageEnhance.Color(img).enhance(1.15)
    img = ImageEnhance.Contrast(img).enhance(1.1)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

    width, height = img.size
    draw = ImageDraw.Draw(img)

    # --- 1. Render Quote Text ---
    font_size = int(style["base_size"] * (1.50 + randint(-5, 5) / 100))  # Increased sizing for larger quote text
    font = _load_font(style["font_family"], font_size)
    max_chars = max(20, int(width / (font_size * 0.60)))  # Better text wrapping for larger fonts
    wrapped = "\n".join(wrap(quote_text, width=max_chars))
    bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=8)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (width - text_w) / 2
    y_offset = style.get("y_offset", 0.0)
    y = (height - text_h) / 2 + (y_offset * height)
    text_color = _auto_color_for_background(img, style["color"])
    shadow_color = (0, 0, 0) if text_color == (255, 255, 255) else (255, 255, 255)
    for dx, dy in [(2, 2), (1, 1)]:
        draw.multiline_text((x + dx, y + dy), wrapped, font=font, fill=shadow_color, align="center", spacing=8)
    _apply_fake_style(draw, x, y, wrapped, font, text_color, style["bold"], style["italic"], "center", spacing=8)

    # --- 2. Add Branding ---
    BRAND_TEXT = "@aiwithsid | http://grwothbrothers.in"
    padding = max(20, int(width * 0.02))

    # Add Brand Text (Bottom Left)
    try:
        # === FONT SIZE FIX IS HERE ===
        brand_font_size = max(20, int(height * 0.04)) # Improved sizing for better visibility
        brand_font = _load_font("sans", brand_font_size)
        text_x = padding
        text_y = height - padding - brand_font_size - 10
        # Stronger shadow for better contrast
        draw.text((text_x + 3, text_y + 3), BRAND_TEXT, font=brand_font, fill=(0, 0, 0))
        draw.text((text_x + 1, text_y + 1), BRAND_TEXT, font=brand_font, fill=(0, 0, 0))
        draw.text((text_x, text_y), BRAND_TEXT, font=brand_font, fill=(255, 255, 255))
    except Exception as e:
        print(f"⚠️  Could not render brand text: {e}")

    # Add Logo (Bottom Right)
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH)
            logo_max_h = int(height * 0.05)
            ratio = logo_max_h / logo.height
            logo_w = int(logo.width * ratio)
            logo.thumbnail((logo_w, logo_max_h), Image.Resampling.LANCZOS)
            logo_x = width - logo.width - padding
            logo_y = height - logo.height - padding
            img.paste(logo, (logo_x, logo_y))
        except Exception as e:
            print(f"⚠️  Could not paste logo: {e}")
    else:
        # === PATH FIX IS HERE ===
        print(f"⚠️  Logo not found at {LOGO_PATH}. Skipping logo branding. Ensure assets folder exists.")
    
    img.convert("RGB").save(output_path, "PNG")
    print(f"✅ Styled typography and branding applied ({mood}). Saved: {output_path}")
    return output_path