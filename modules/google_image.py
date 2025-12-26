import os
import json
import requests
import base64
from typing import Optional
from google.oauth2 import service_account
from google.auth.transport.requests import Request as GoogleAuthRequest
from .utils import ensure_dir, get_env

# --- CONFIGURATION ---
CREDENTIALS_PATH = "credentials.json"
LOCATION = "us-central1"
# We target Imagen 3.0 directly via the API
MODEL_ID = "imagen-3.0-generate-001" 

def get_access_token(creds_path):
    """
    Manually gets a Google Cloud Access Token using the JSON key.
    This avoids using the heavy Vertex AI SDK and prevents import errors.
    """
    try:
        # Load credentials directly from file
        creds = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        # Refresh to get the actual token string
        creds.refresh(GoogleAuthRequest())
        return creds.token, creds.project_id
    except Exception as e:
        print(f"❌ Auth Error: {e}")
        return None, None

def generate_image(prompt: str, output_path: str, mode: str = "motivational") -> Optional[str]:
    """
    Generates an image using Google Vertex AI via RAW REST API.
    CRITICAL FIX: Bypasses 'vertexai' library imports to prevent startup crashes.
    """
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"❌ Missing Credentials: {CREDENTIALS_PATH} not found.")
        return None

    ensure_dir(output_path)

    # 1. Authenticate (No Vertex SDK used)
    print("🔑 Authenticating with credentials.json...")
    token, project_id = get_access_token(CREDENTIALS_PATH)
    if not token:
        print("❌ Failed to generate auth token.")
        return None

    # 2. Prepare Endpoint URL
    # Direct access to the prediction endpoint
    api_endpoint = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{LOCATION}/publishers/google/models/{MODEL_ID}:predict"

    # 3. Enhance Prompt
    final_prompt = f"{prompt}, photorealistic, 8k, cinematic lighting"
    if mode == "motivational":
        final_prompt += ", minimalist, inspiring, soft focus, no text"

    # 4. Construct Payload (Raw JSON)
    payload = {
        "instances": [
            {
                "prompt": final_prompt
            }
        ],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "1:1"
        }
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    print(f"🎨 Sending request to Vertex AI ({MODEL_ID})...")
    
    try:
        response = requests.post(api_endpoint, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            response_json = response.json()
            predictions = response_json.get("predictions", [])
            
            if predictions:
                # Vertex AI returns Base64 encoded string
                b64_data = predictions[0]["bytesBase64Encoded"]
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(b64_data))
                print(f"✅ Image generated successfully → {output_path}")
                return output_path
            else:
                print(f"⚠️ API returned 200 but no image data: {response_json}")
                
        else:
            print(f"❌ Vertex API Error {response.status_code}: {response.text}")
            if response.status_code == 404:
                print("💡 DEBUG: Check if 'us-central1' is the correct region for your project.")
            if response.status_code == 403:
                print("💡 DEBUG: Ensure 'Vertex AI API' is enabled in Cloud Console.")

    except Exception as e:
        print(f"❌ Connection failed: {e}")

    return None
