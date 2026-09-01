"""
Sort campus gallery photos (11.jpg - 90.jpg) into category folders using CLIP.

Each image is assigned to its SINGLE best-matching category (highest similarity
score) and then copied or moved into images/sorted/<category>/.

Usage:
    python sort_campus_photos.py            # copies files (safe, default)
    python sort_campus_photos.py --move      # moves files instead of copying

Requires:
    pip install open_clip_torch pillow torch

Expects your images in an "images/" folder next to this script,
named 11.jpg through 90.jpg (change IMAGE_DIR / IMAGE_RANGE below if different).
"""

import os
import sys
import shutil
from PIL import Image
import torch
import open_clip

# ---- CONFIG ----
IMAGE_DIR = ""
OUTPUT_DIR = os.path.join(IMAGE_DIR, "sorted")
IMAGE_RANGE = range(11, 91)  # 11.jpg to 90.jpg

CATEGORIES = {
    "hostel":     ["a photo of a school hostel dormitory", "students in a hostel room", "beds in a dormitory"],
    "sports":     ["a photo of students playing sports", "a school sports ground", "children playing a game outdoors"],
    "arts":       ["a photo of students doing arts and crafts", "a cultural dance or music performance", "an art or craft classroom"],
    "coaching":   ["a photo of students studying in a classroom", "a coaching or tuition class", "students taking an exam"],
    "academic":   ["a photo of a classroom lecture", "a school library", "a science laboratory", "a computer lab"],
    "campus":     ["a photo of a school building exterior", "a school campus with grounds and trees", "the entrance gate of a school"],
    "events":     ["a photo of a school annual day function", "students performing on stage", "an award or prize distribution ceremony"],
    "assembly":   ["a photo of school morning assembly", "students standing in line for prayer", "a school flag hoisting ceremony"],
    "excursion":  ["a photo of a school field trip", "students on an educational excursion", "students visiting a museum or factory"],
    "faculty":    ["a group photo of school teachers and staff", "a teacher standing in a classroom"],
    "students":   ["a group photo of school students", "students posing together outdoors"],
    "canteen":    ["a photo of a school canteen or dining hall", "students eating in a mess hall"],
}
# ------------------


def main():
    move_files = "--move" in sys.argv
    action = "Moving" if move_files else "Copying"

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading CLIP model on {device}...")
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="openai"
    )
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    model.to(device).eval()

    # Collect image paths that actually exist
    image_paths = []
    for i in IMAGE_RANGE:
        for ext in ("jpg", "jpeg", "png"):
            p = os.path.join(IMAGE_DIR, f"{i}.{ext}")
            if os.path.exists(p):
                image_paths.append(p)
                break

    if not image_paths:
        print(f"No images found in '{IMAGE_DIR}/'. Check IMAGE_DIR and file names.")
        return

    print(f"Found {len(image_paths)} images. Encoding...")

    # Encode all images once
    image_features = []
    valid_paths = []
    with torch.no_grad():
        for p in image_paths:
            try:
                img = preprocess(Image.open(p).convert("RGB")).unsqueeze(0).to(device)
                feat = model.encode_image(img)
                feat /= feat.norm(dim=-1, keepdim=True)
                image_features.append(feat)
                valid_paths.append(p)
            except Exception as e:
                print(f"  Skipping {p}: {e}")

    image_features = torch.cat(image_features, dim=0)  # shape: [N, dim]

    # Encode category text prompts (averaged per category)
    cat_names = list(CATEGORIES.keys())
    cat_embeddings = []
    with torch.no_grad():
        for cat in cat_names:
            prompts = CATEGORIES[cat]
            text_tokens = tokenizer(prompts).to(device)
            text_features = model.encode_text(text_tokens)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            cat_embedding = text_features.mean(dim=0, keepdim=True)
            cat_embedding /= cat_embedding.norm(dim=-1, keepdim=True)
            cat_embeddings.append(cat_embedding)
    cat_embeddings = torch.cat(cat_embeddings, dim=0)  # shape: [num_categories, dim]

    # For each image, find its single best-matching category
    with torch.no_grad():
        sims = image_features @ cat_embeddings.T  # shape: [N, num_categories]
        best_cat_idx = sims.argmax(dim=1)
        best_scores = sims.max(dim=1).values

    # Make output folders
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for cat in cat_names:
        os.makedirs(os.path.join(OUTPUT_DIR, cat), exist_ok=True)

    # Move/copy each file into its category folder
    print(f"\n{action} files into '{OUTPUT_DIR}/<category>/'...\n")
    assignments = {cat: [] for cat in cat_names}
    for path, idx, score in zip(valid_paths, best_cat_idx.tolist(), best_scores.tolist()):
        cat = cat_names[idx]
        dest = os.path.join(OUTPUT_DIR, cat, os.path.basename(path))
        if move_files:
            shutil.move(path, dest)
        else:
            shutil.copy2(path, dest)
        assignments[cat].append((os.path.basename(path), score))

    # Print summary
    print("=== Sorting summary ===\n")
    for cat in cat_names:
        files = assignments[cat]
        print(f"[{cat.upper()}] — {len(files)} photo(s)")
        for fname, score in sorted(files, key=lambda x: -x[1]):
            print(f"  {fname}   (score: {score:.3f})")
        print()

    print(f"Done. {action.lower()} complete. Review low-confidence scores manually —")
    print("CLIP isn't perfect, especially for categories like 'events' vs 'academic'.")


if __name__ == "__main__":
    main()