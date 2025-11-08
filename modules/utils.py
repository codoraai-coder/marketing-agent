import os
from dotenv import load_dotenv
from PIL import ImageStat, Image

load_dotenv()

def get_env(key: str, default=None):
    return os.getenv(key, default)

def print_header(title: str):
    bar = "=" * max(20, len(title) + 2)
    print(f"\n{bar}\n {title}\n{bar}\n")

def image_luminance(img: Image.Image) -> float:
    g = img.convert("L")
    return ImageStat.Stat(g).mean[0]

def ensure_dir(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
