# modules/blog_agent/diagram_generator.py
import os
import subprocess
from modules.text_generator import _gemini_call, validate_mermaid_code
from modules.utils import ensure_dir

def generate_mermaid_from_context(topic: str, description: str, context: str) -> str:
    prompt = (
        "Generate a logically correct Mermaid.js diagram using the context below.\n"
        "Use 5–8 nodes with meaningful names and clear data/process flow.\n"
        "Return ONLY Mermaid code beginning with 'graph'.\n\n"
        f"Topic: {topic}\n"
        f"Diagram goal: {description}\n\n"
        f"Context:\n{context}\n"
    )
    code = (_gemini_call(prompt) or "").strip()
    if not code.startswith("graph"):
        code = "graph LR\nA[Input]-->B[Process]\nB-->C[Output]\nC-->D[Feedback]\nD-->A"
    return validate_mermaid_code(code, topic)

def render_mermaid(code: str, output_dir: str, file_stem: str) -> tuple[str|None, str]:
    """
    Save .mmd and try to render to PNG using Mermaid CLI (mmdc).
    Returns (png_path_or_None, mmd_path)
    """
    ensure_dir(os.path.join(output_dir, "x"))
    mmd_path = os.path.join(output_dir, f"{file_stem}.mmd")
    png_path = os.path.join(output_dir, f"{file_stem}.png")

    with open(mmd_path, "w", encoding="utf-8") as f:
        f.write(code)

    try:
        subprocess.run(["mmdc", "-i", mmd_path, "-o", png_path, "-b", "transparent"], check=True)
        return png_path, mmd_path
    except Exception as e:
        print("⚠️ Mermaid CLI not available or render failed:", e)
        return None, mmd_path
