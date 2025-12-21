import os
import sys
import uvicorn
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# --- 1. Project Setup ---
# Add modules to path (from main.py)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load Environment Variables (.env)
load_dotenv()

# --- 2. Import Core Agent Logic & S3 Storage ---
try:
    from modules.content_builder import build_content_from_prompt
    from modules.blog_agent.blog_builder import build_blog_from_topic
    from modules.text_generator import _gemini_call
    # New S3 Import
    from modules.s3_storage import upload_to_s3
except ImportError as e:
    print(f"ERROR: Failed to import core modules: {e}")
    print("Please ensure the 'modules' directory is in the same folder and includes s3_storage.py.")
    sys.exit(1)


# --- 3. FastAPI App & API Models ---

app = FastAPI(
    title="AI Content Agent API",
    description="API for the Motivational Post and RAG Blog Generation pipelines with S3 Storage.",
    version="1.1.0"
)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Request Models ---
class TopicRequest(BaseModel):
    topic: str = Field(..., example="The Future of AI")

class ChatRequest(BaseModel):
    prompt: str

# --- API Response Models ---
class ChatResponse(BaseModel):
    text: str

class MotivationalPostResponse(BaseModel):
    topic: str
    quote_text: str
    # Changed from image_path to image_url
    image_url: str = Field(..., example="https://my-bucket.s3.amazonaws.com/posts/final_quote_image.png")

class BlogResponse(BaseModel):
    topic: str
    # Changed from local paths to S3 URLs
    docx_url: str = Field(..., example="https://my-bucket.s3.amazonaws.com/blogs/docs/blog.docx")
    cover_url: Optional[str] = Field(None, example="https://my-bucket.s3.amazonaws.com/blogs/covers/cover.png")
    # Removed assets_dir as it is a local path and less relevant for cloud deployments


# --- 4. API Endpoints ---

@app.get("/health", summary="Health Check")
def health():
    """A simple endpoint to confirm the server is running."""
    return {"status": "ok"}

@app.post("/api/v1/chat", 
          response_model=ChatResponse, 
          summary="Simple Chat")
def chat(req: ChatRequest):
    """Provides a direct interface to the Gemini text generator."""
    text = _gemini_call(req.prompt)
    return ChatResponse(text=text)

@app.post("/api/v1/generate/motivational_post", 
          response_model=MotivationalPostResponse, 
          summary="Module 1: Generate Motivational Post")
def generate_motivational_post(req: TopicRequest):
    """
    Runs the full 'Pipeline 1' (Motivational Post Generator).
    Generates locally, uploads to S3, and returns the public URL.
    """
    print(f"Received request to generate motivational post for topic: {req.topic}")
    try:
        # 1. Generate locally
        data, local_image_path = build_content_from_prompt(req.topic)
        
        if not local_image_path:
            raise HTTPException(status_code=500, detail="Image generation failed internally.")

        # 2. Upload to S3
        # We upload to a 'posts' folder in the bucket
        s3_url = upload_to_s3(local_image_path, folder="posts")
        
        if not s3_url:
            raise HTTPException(status_code=500, detail="Failed to upload generated image to S3.")
            
        return MotivationalPostResponse(
            topic=req.topic,
            quote_text=data.get("quote_text", ""),
            image_url=s3_url
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in motivational post: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/generate/blog_post", 
          response_model=BlogResponse, 
          summary="Module 2: Generate RAG Blog Post")
def generate_blog_post(req: TopicRequest):
    """
    Runs the full 'Pipeline 2' (Blog Post Generator).
    Generates DOCX and Cover locally, uploads to S3, and returns public URLs.
    """
    print(f"Received request to generate blog post for topic: {req.topic}")
    try:
        # 1. Generate locally
        # build_blog_from_topic returns (docx_path, cover_path, assets_dir)
        local_docx_path, local_cover_path, _ = build_blog_from_topic(req.topic)

        # 2. Upload DOCX to S3
        docx_url = upload_to_s3(local_docx_path, folder="blogs/docs")
        if not docx_url:
             raise HTTPException(status_code=500, detail="Failed to upload Blog DOCX to S3.")

        # 3. Upload Cover to S3 (if it exists)
        cover_url = None
        if local_cover_path:
            cover_url = upload_to_s3(local_cover_path, folder="blogs/covers")

        return BlogResponse(
            topic=req.topic,
            docx_url=docx_url,
            cover_url=cover_url
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in blog post: {e}")
        raise HTTPException(status_code=500, detail=f"Blog generation failed. Error: {str(e)}")

# --- 5. Server Entry Point ---

if __name__ == "__main__":
    """
    Allows running the server directly with: python api.py
    """
    print("Starting AI Content Agent API server (S3 Enabled)...")
    uvicorn.run(
        "api:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=True
    )