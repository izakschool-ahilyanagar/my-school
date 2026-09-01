"""
Generate a tabbed / filterable campus gallery HTML snippet from the
category folders created by sort_campus_photos.py.

Reads:   images/sorted/<category>/*.jpg
Writes:  gallery_output.html  (paste this into index.html)

Usage:
    python generate_gallery_html.py
"""

import os
import glob

SORTED_DIR = os.path.join("", "sorted")
OUTPUT_FILE = "gallery_output.html"

# Nicer display labels for category folder names (edit as you like)
LABELS = {
    "hostel": "Hostel",
    "sports": "Sports",
    "arts": "Arts & Culture",
    "coaching": "Coaching",
    "academic": "Academics",
    "campus": "Campus",
    "events": "Events",
    "assembly": "Assembly",
    "excursion": "Excursions",
    "faculty": "Faculty",
    "students": "Students",
    "canteen": "Canteen",
}


def main():
    if not os.path.isdir(SORTED_DIR):
        print(f"Couldn't find '{SORTED_DIR}'. Run sort_campus_photos.py first.")
        return

    categories = sorted(
        d for d in os.listdir(SORTED_DIR)
        if os.path.isdir(os.path.join(SORTED_DIR, d))
    )

    if not categories:
        print(f"No category folders found inside '{SORTED_DIR}'.")
        return

    # Collect image files per category (keep original filenames, e.g. 11.jpg)
    cat_images = {}
    for cat in categories:
        files = []
        for ext in ("jpg", "jpeg", "png"):
            files += glob.glob(os.path.join(SORTED_DIR, cat, f"*.{ext}"))
        files = sorted(files, key=lambda p: os.path.basename(p))
        if files:
            cat_images[cat] = files

    if not cat_images:
        print("No images found inside category folders.")
        return

    print("Found categories:")
    for cat, files in cat_images.items():
        print(f"  {LABELS.get(cat, cat.title())}: {len(files)} photo(s)")

    # ---- Build tab buttons ----
    tab_buttons = ['<button class="gallery-tab px-4 py-1.5 rounded-full text-[13px] font-mono uppercase tracking-wide border border-ruledark text-inktext bg-lime text-papertext" data-filter="all">All</button>']
    for cat in cat_images:
        label = LABELS.get(cat, cat.title())
        tab_buttons.append(
            f'<button class="gallery-tab px-4 py-1.5 rounded-full text-[13px] font-mono uppercase tracking-wide border border-ruledark text-inktext hover:bg-ruledark" data-filter="{cat}">{label}</button>'
        )
    tabs_html = "\n".join(tab_buttons)

    # ---- Build image tiles (all in one scrollable row, tagged by category) ----
    image_tiles = []
    for cat, files in cat_images.items():
        for f in files:
            fname = os.path.basename(f)
            # source path as it will be served on the live site (images/<file>, not images/sorted/<cat>/<file>)
            src = f"images/{fname}"
            image_tiles.append(
                f'<div class="gallery-item snap-start shrink-0 w-[280px] sm:w-[360px] md:w-[400px]" data-category="{cat}">\n'
                f'<img src="{src}" alt="Campus photo - {LABELS.get(cat, cat)}" loading="lazy" '
                f'class="w-[280px] sm:w-[360px] md:w-[400px] h-[340px] sm:h-[420px] md:h-[460px] object-cover rounded border border-ruledark">\n'
                f'</div>'
            )
    images_html = "\n".join(image_tiles)

    section = f"""
<!-- ============ CAMPUS PHOTO GALLERY (categorized) ============ -->
<section class="bg-ink text-inktext pb-24 md:pb-32">
<div class="max-w-6xl mx-auto px-5 sm:px-8">
<div class="reveal flex justify-between items-end gap-10 flex-wrap mb-6">
<h3 class="text-2xl sm:text-3xl font-semibold">Campus gallery.</h3>
<p class="max-w-[38ch] text-inktextdim text-[15px]">A look around Bhalwani campus — drag, swipe, or scroll to see more.</p>
</div>
<div class="reveal flex flex-wrap gap-2 mb-6">
{tabs_html}
</div>
</div>
<div class="reveal max-w-6xl mx-auto px-5 sm:px-8">
<div id="campusGallery" class="flex gap-4 overflow-x-auto no-scrollbar snap-x snap-mandatory pb-2 cursor-grab active:cursor-grabbing select-none">
{images_html}
</div>
</div>
</section>

<script>
(function() {{
  const gallery = document.getElementById('campusGallery');
  if (!gallery) return;

  // Wheel -> horizontal scroll (desktop convenience)
  gallery.addEventListener('wheel', (e) => {{
    if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {{
      e.preventDefault();
      gallery.scrollLeft += e.deltaY;
    }}
  }}, {{ passive: false }});

  // Click-and-drag scrolling (desktop mouse users)
  let isDown = false, startX, scrollLeftStart;
  gallery.addEventListener('mousedown', (e) => {{
    isDown = true;
    startX = e.pageX - gallery.offsetLeft;
    scrollLeftStart = gallery.scrollLeft;
  }});
  window.addEventListener('mouseup', () => {{ isDown = false; }});
  gallery.addEventListener('mouseleave', () => {{ isDown = false; }});
  gallery.addEventListener('mousemove', (e) => {{
    if (!isDown) return;
    e.preventDefault();
    const x = e.pageX - gallery.offsetLeft;
    const walk = (x - startX) * 1.2;
    gallery.scrollLeft = scrollLeftStart - walk;
  }});

  // Category filter tabs
  const tabs = document.querySelectorAll('.gallery-tab');
  const items = document.querySelectorAll('.gallery-item');
  tabs.forEach(tab => {{
    tab.addEventListener('click', () => {{
      const filter = tab.dataset.filter;

      tabs.forEach(t => {{
        t.classList.remove('bg-lime', 'text-papertext');
        t.classList.add('hover:bg-ruledark');
      }});
      tab.classList.add('bg-lime', 'text-papertext');
      tab.classList.remove('hover:bg-ruledark');

      items.forEach(item => {{
        const show = filter === 'all' || item.dataset.category === filter;
        item.style.display = show ? '' : 'none';
      }});

      gallery.scrollLeft = 0;
    }});
  }});
}})();
</script>
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(section)

    print(f"\nWrote {OUTPUT_FILE} — paste this into index.html in place of your current gallery section.")
    print("Note: img src paths point to 'images/<file>.jpg' (your live images folder),")
    print("      not 'images/sorted/...' — make sure your final images live at that flat path on the site.")


if __name__ == "__main__":
    main()