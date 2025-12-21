# modules/blog_agent/blog_builder.py

import os
import uuid
from modules.utils import print_header, ensure_dir
from modules.text_generator import plan_blog_outline
from modules.blog_agent.retriever_hybrid import find_and_download_image
from modules.blog_agent.writer import write_sections
from modules.blog_agent.visual_agent import decide_visuals_for_section
from modules.blog_agent.formatter import assemble_docx

def _insert_after_paragraphs(content: str, insert_md: str, after_paragraph: int) -> str:
    """Inserts a markdown block after the Nth paragraph."""
    paras = [p for p in content.split("\n\n") if p.strip() != ""]
    idx = max(0, min(after_paragraph, len(paras)))
    new = []
    for i, p in enumerate(paras):
        new.append(p)
        if i == idx:
            new.append(insert_md)
    if idx >= len(paras):
        new.append(insert_md)
    return "\n\n".join(new)

def build_blog_from_topic(topic: str):
    """
    Full RAG-enhanced blog pipeline with UNIQUE filenames.
    """
    # Create unique run ID
    run_id = uuid.uuid4().hex[:8]
    
    print_header("Planning Blog Structure")
    plan_dict = plan_blog_outline(topic)

    print_header("Writing Sections")
    raw_sections = write_sections(plan_dict, topic)

    print_header("Finding Cover Image with RAG")
    # Unique cover path
    cover_filename = f"generated/blogs/assets/cover_{run_id}.png"
    cover_path = find_and_download_image(
        topic=topic,
        keywords="technology abstract cover",
        vtype="image",
        output_path=cover_filename
    )

    print_header("Enhancing Sections with RAG Visuals")
    sections_with_md = []
    ensure_dir("generated/blogs/assets/x")

    for s_idx, (heading, content) in enumerate(raw_sections):
        visuals = decide_visuals_for_section(heading, content)
        enriched = content

        for v_idx, v in enumerate(visuals):
            keywords = v["keywords"]
            vtype = v["type"]
            after = v["after_paragraph"]
            
            # Unique filename for section images
            clean_keywords = keywords.replace(' ', '_')[:20] # Keep it short
            stem = f"sec{s_idx}_vis{v_idx}_{clean_keywords}_{run_id}.png"
            out_path = os.path.join("generated/blogs/assets", stem)
            
            img_path = find_and_download_image(
                topic=topic,
                keywords=keywords,
                vtype=vtype,
                output_path=out_path
            )

            if img_path:
                rel = os.path.relpath(img_path, "generated/blogs").replace("\\","/")
                block = f"![{keywords}]({rel})" 
            else:
                block = f"> (Image not found for keywords: {keywords})"

            enriched = _insert_after_paragraphs(enriched, block, after)

        sections_with_md.append((heading, enriched))

    print_header("Assembling DOCX Blog")
    # Pass the run_id to assembler
    docx_path = assemble_docx(plan_dict, sections_with_md, cover_path, topic, run_id=run_id)

    return docx_path, cover_path, "generated/blogs/assets"