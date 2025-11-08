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

# --- 2. Import Core Agent Logic ---
# These modules power the pipelines described in your documentation
try:
    from modules.content_builder import build_content_from_prompt
    from modules.blog_agent.blog_builder import build_blog_from_topic
    from modules.text_generator import _gemini_call
except ImportError as e:
    print(f"ERROR: Failed to import core modules: {e}")
    print("Please ensure the 'modules' directory is in the same folder.")
    sys.exit(1)


# --- 3. FastAPI App & API Models ---

app = FastAPI(
    title="AI Content Agent API",
    description="API for the Motivational Post and RAG Blog Generation pipelines.",
    version="1.0.0"
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
    image_path: str = Field(..., example="generated/final_quote_image.png")

class BlogResponse(BaseModel):
    topic: str
    docx_path: str = Field(..., example="generated/blogs/blog.docx")
    cover_path: Optional[str] = Field(None, example="generated/blogs/assets/cover.png")
    assets_dir: str = Field(..., example="generated/blogs/assets")


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
    
    Generates a styled quote image with branding from a single topic [cite: 43-44].
    """
    print(f"Received request to generate motivational post for topic: {req.topic}")
    try:
        data, image_path = build_content_from_prompt(req.topic)
        
        if not image_path:
            raise HTTPException(status_code=500, detail="Image generation failed. Check Stability AI API key and logs.")
            
        return MotivationalPostResponse(
            topic=req.topic,
            quote_text=data.get("quote_text", ""),
            image_path=image_path
        )
    except Exception as e:
        print(f"ERROR in motivational post: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/generate/blog_post", 
          response_model=BlogResponse, 
          summary="Module 2: Generate RAG Blog Post")
def generate_blog_post(req: TopicRequest):
    """
    Runs the full 'Pipeline 2' (Blog Post Generator).
    
    Generates a RAG-enhanced technical blog post as a .docx file[cite: 71, 74].
    """
    print(f"Received request to generate blog post for topic: {req.topic}")
    try:
        docx_path, cover_path, assets_dir = build_blog_from_topic(req.topic)
        return BlogResponse(
            topic=req.topic,
            docx_path=docx_path,
            cover_path=cover_path,
            assets_dir=assets_dir
        )
    except Exception as e:
        print(f"ERROR in blog post: {e}")
        raise HTTPException(status_code=500, detail=f"Blog generation failed. Check Gemini/SerpAPI keys and logs. Error: {str(e)}")

# --- 5. Server Entry Point ---

if __name__ == "__main__":
    """
    Allows running the server directly with: python api_server.py
    """
    print("Starting AI Content Agent API server...")
    uvicorn.run(
        "api_server:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=True
    )