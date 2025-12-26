import os
import vertexai
from vertexai.preview.vision import ImageGenerationModel
from .utils import ensure_dir, get_env
from typing import Optional

# --- CONFIGURATION ---
# We assume the credentials.json file is in the root directory
CREDENTIALS_PATH = "credentials.json"
PROJECT_ID = get_env("GOOGLE_CLOUD_PROJECT_ID") # You'll need to add this to .env, or hardcode it
LOCATION = "us-central1" # Imagen is most stable in us-central1

def generate_image(prompt: str, output_path: str, mode: str = "motivational") -> Optional[str]:
    """
    Generates an image using Google Vertex AI (Imagen 3).
    Requires 'credentials.json' and 'google-cloud-aiplatform'.
    """
    
    # 1. Setup Auth
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"❌ Missing Credentials: Could not find '{CREDENTIALS_PATH}'")
        return None

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
    
    ensure_dir(output_path)
    
    # 2. Extract Project ID from JSON if not in env
    # This is a helper so you don't strictly need to edit .env
    project_id = PROJECT_ID
    if not project_id:
        import json
        try:
            with open(CREDENTIALS_PATH) as f:
                creds = json.load(f)
                project_id = creds.get("project_id")
        except Exception:
            print("❌ Could not read project_id from credentials.json")
            return None

    print(f"🎨 Initializing Vertex AI (Project: {project_id})...")
    
    try:
        vertexai.init(project=project_id, location=LOCATION)
        
        # 3. Load Model (Imagen 3.0)
        # Options: 'imagen-3.0-generate-001' or 'imagegeneration@006' (Imagen 2)
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        
        # 4. Enhance Prompt
        final_prompt = f"{prompt}, photorealistic, 8k, cinematic lighting"
        if mode == "motivational":
            final_prompt += ", minimalist, inspiring, soft focus, no text"
            
        print(f"🚀 Generating with Imagen 3.0: '{final_prompt[:50]}...'")
        
        # 5. Generate
        images = model.generate_images(
            prompt=final_prompt,
            number_of_images=1,
            language="en",
            aspect_ratio="1:1",
            safety_filter_level="block_some",
            person_generation="allow_adult"
        )
        
        if images:
            # Save the first image
            images[0].save(location=output_path, include_generation_parameters=False)
            print(f"✅ Image saved to {output_path}")
            return output_path
            
    except Exception as e:
        print(f"❌ Vertex AI Error: {e}")
        if "403" in str(e):
            print("💡 TIP: Ensure 'Vertex AI API' is enabled in Cloud Console.")
        if "404" in str(e):
            print("💡 TIP: Check if 'us-central1' supports Imagen 3 for your project.")

    return None
