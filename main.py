import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.utils import print_header
from modules.content_builder import (
    build_content_from_prompt,
    generate_caption_for_platform,
    generate_platform_hashtags,
)
from modules.blog_agent.blog_builder import build_blog_from_topic

def main():
    print_header("AI Content Agent")
    print("1) Motivational Post")
    print("2) Innovation / Tech Blog (Hybrid RAG + Generative)")
    mode = input("Enter your choice (1 or 2): ").strip()

    if mode == "1":
        topic = input("Enter your motivational topic: ").strip()
        data, image_path = build_content_from_prompt(topic)

        print_header("Platform Selection")
        print("1) Twitter (X)\n2) Instagram\n3) Facebook\n4) LinkedIn\n5) Threads")
        platform = {"1":"Twitter","2":"Instagram","3":"Facebook","4":"LinkedIn","5":"Threads"}.get(input("Enter platform choice (1-5): ").strip(),"LinkedIn")

        caption = generate_caption_for_platform(platform, data["topic"], data["tone"])
        hashtags = generate_platform_hashtags(platform, data["topic"], caption)
        print_header("FINAL POST")
        print(f"Platform: {platform}")
        print("\nCaption:\n" + caption)
        print("\nHashtags:\n" + " ".join(hashtags))
        if image_path: print(f"\nImage: {image_path}")
        print("\n✅  Done.")

    elif mode == "2":
        topic = ""
        while not topic:
            topic = input("Enter the technology/topic for the blog (e.g., 'Convolutional Neural Network'): ").strip()
            if not topic:
                print("Topic cannot be empty. Please try again.")

        docx_path, cover_path, assets_dir = build_blog_from_topic(topic)

        print_header("BLOG GENERATED")
        print(f"Word Document: {docx_path}")
        if cover_path: print(f"Cover Image: {cover_path}")
        print(f"Assets Folder: {assets_dir}")
        print("\n✅  Blog ready.")
    else:
        print("Invalid option selected. Please run again and choose '1' or '2'.")

if __name__ == "__main__":
    main()