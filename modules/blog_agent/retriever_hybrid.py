# modules/blog_agent/retriever_hybrid.py
import requests
import os
from modules.utils import get_env, ensure_dir

# --- Configuration ---
SERP_API_KEY = get_env("SERP_API_KEY")

# --- API Self-Test ---
IS_API_KEY_VALID = None

def _validate_api_key():
    """
    Performs a one-time, simple search to check if the SerpAPI key is valid.
    Uses google_images as the default test.
    """
    global IS_API_KEY_VALID
    if IS_API_KEY_VALID is not None:
        return IS_API_KEY_VALID

    if not SERP_API_KEY:
        print("❌ CRITICAL: SERP_API_KEY is missing from your environment file (.env).")
        IS_API_KEY_VALID = False
        return False

    print("🩺 Performing a one-time check of the SerpAPI key...")
    try:
        params = {"q": "Test", "engine": "google_images", "api_key": SERP_API_KEY}
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        
        if response.status_code == 200:
            print("✅ SerpAPI key is valid.")
            IS_API_KEY_VALID = True
            return True
        else:
            error_data = response.json()
            error_message = error_data.get("error", "An unknown API error occurred.")
            print(f"❌ CRITICAL: SerpAPI key appears to be invalid. Reason: {error_message}")
            print("   Please check your SERP_API_KEY in your .env file and ensure your account has searches remaining.")
            IS_API_KEY_VALID = False
            return False
            
    except Exception as e:
        print(f"❌ CRITICAL: Failed to connect to SerpAPI. Check your network connection. Error: {e}")
        IS_API_KEY_VALID = False
        return False

def find_and_download_image(topic: str, keywords: str, vtype: str, output_path: str) -> str | None:
    """
    Uses a multi-engine, multi-attempt "Query Cascade" RAG strategy.
    It will try Google Images first, then Bing Images as a fallback.
    """
    if not _validate_api_key():
        return None

    search_queries = [
        f"{topic} {keywords} {vtype}", # Attempt 1: Specific
        f"{topic} {keywords}",         # Attempt 2: Simpler
        f"{keywords}"                  # Attempt 3: Broadest
    ]

    for query in search_queries:
        # --- Try Google Images First ---
        print(f"🔎 [Google] Searching for: '{query}'")
        image_url = _search_with_engine(query, "google_images")
        
        if image_url and _download_image(image_url, output_path):
            return output_path # Success!

        # --- If Google fails, Try Bing Images ---
        print(f"⚠️  [Google] failed. Trying [Bing] for: '{query}'")
        image_url = _search_with_engine(query, "bing_images")
        
        if image_url and _download_image(image_url, output_path):
            return output_path # Success!

    # --- Final Fallback ---
    print(f"⚠️ All specific searches failed. Trying a broad fallback search.")
    fallback_query = f"{topic} {vtype}"
    image_url = _search_with_engine(fallback_query, "google_images")
    if image_url and _download_image(image_url, output_path):
        return output_path

    print(f"❌ All search attempts on all engines failed for keywords: '{keywords}'")
    return None

def _search_with_engine(query: str, engine: str) -> str | None:
    """Helper function to perform the SerpAPI search on a specific engine."""
    try:
        params = { "q": query, "engine": engine, "ijn": "0", "api_key": SERP_API_KEY }
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
        response.raise_for_status()
        results = response.json()

        if "images_results" in results and results["images_results"]:
            for image_info in results["images_results"][:3]:
                # --- This is the key fix ---
                # Check for Google's key OR Bing's key
                url = image_info.get("original") or image_info.get("original_image_url")
                if url:
                    return url
            
    except Exception as e:
        print(f"❌ Error during [{engine}] search for '{query}': {e}")
    
    print(f"❌ No image results found on [{engine}] for query: '{query}'")
    return None

def _download_image(url: str, output_path: str) -> str | None:
    """Helper function to download an image from a URL."""
    try:
        print(f"Attempting to download from: {url}")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        image_response = requests.get(url, timeout=30, headers=headers, stream=True)
        image_response.raise_for_status()
        ensure_dir(output_path)
        with open(output_path, "wb") as f:
            for chunk in image_response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Image downloaded successfully -> {output_path}")
        return output_path
    except Exception as e:
        print(f"⚠️  Failed to download {url}. Reason: {e}.")
        return None