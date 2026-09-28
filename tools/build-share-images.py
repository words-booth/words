"""Render link-preview images and Open Graph tags for every quote and poem.

Run after adding or editing a quote or poem:

    python3 tools/build-share-images.py

Requires Google Chrome. Writes JPEGs to share/ and updates the <head> of each page.
"""
import html
import os
import re
import shutil
import subprocess
import tempfile

SITE = "https://words.booth.us.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
WIDTH, HEIGHT = 1200, 630
# Headless Chrome reserves part of the window for hidden browser UI, so render a
# taller window with the image area centred, then crop the centre.
WINDOW_HEIGHT = 900
TOP = (WINDOW_HEIGHT - HEIGHT) // 2

FRAME = """<!doctype html>
<html><head><meta charset="utf-8"><style>
  html, body {{ margin: 0; overflow: hidden; }}
  .frame {{ position: absolute; top: {top}px; left: 0; width: {w}px; height: {h}px; overflow: hidden; border: 0; }}
</style></head><body>{content}</body></html>
"""

CARD = """<div class="frame card-bg"><style>
  .card-bg {{
    display: flex; align-items: center; justify-content: center;
    background: radial-gradient(ellipse at 50% 40%, #fbf9f3 0%, #f5f2ea 70%);
    color: #3a3a36; -webkit-font-smoothing: antialiased;
    font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  }}
  .card {{ width: 1000px; height: 510px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }}
  .quote {{ font-size: 46px; line-height: 1.5; }}
  .rule {{ width: 180px; height: 1px; background: #d9d4c6; margin: 38px 0 24px; flex: none; }}
  .author {{ font: 600 17px/1.4 "Helvetica Neue", Helvetica, Arial, sans-serif; letter-spacing: .24em; text-transform: uppercase; color: #6f8471; }}
</style>
  <div class="card">
    <div class="quote">{quote}</div>
    <div class="rule"></div>
    <div class="author">{author}</div>
  </div>
  <script>
    const card = document.querySelector(".card"), q = document.querySelector(".quote");
    let size = 46;
    while (size > 18 && (card.scrollHeight > card.clientHeight || q.scrollWidth > card.clientWidth)) {{
      q.style.fontSize = (size -= 1) + "px";
    }}
  </script>
</div>"""


def screenshot(tmp, content, out):
    wrapper = os.path.join(tmp, "frame.html")
    png = os.path.join(tmp, "shot.png")
    with open(wrapper, "w", encoding="utf-8") as f:
        f.write(FRAME.format(top=TOP, w=WIDTH, h=HEIGHT, content=content))
    subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
         "--force-device-scale-factor=1", f"--window-size={WIDTH},{WINDOW_HEIGHT}",
         "--virtual-time-budget=3000", f"--screenshot={png}", f"file://{wrapper}"],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    # WhatsApp drops preview images much larger than ~300 KB, so ship JPEGs.
    subprocess.run(["sips", "-c", str(HEIGHT), str(WIDTH), "-s", "format", "jpeg",
                    "-s", "formatOptions", "85", png, "--out", out],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def text(fragment):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def set_meta(page, tags):
    page = re.sub(r"\n  <!-- share -->.*?<!-- /share -->", "", page, flags=re.S)
    block = "\n  <!-- share -->\n" + "".join(
        f'  <meta {"name" if k.startswith("twitter:") else "property"}="{k}" content="{html.escape(v)}">\n'
        for k, v in tags
    ) + "  <!-- /share -->"
    return re.sub(r"(<title>.*?</title>)", lambda m: m.group(1) + block, page, count=1)


def tags_for(title, description, rel_page, rel_image):
    return [
        ("og:type", "article"),
        ("og:site_name", "Words"),
        ("og:title", title),
        ("og:description", description),
        ("og:url", f"{SITE}/{rel_page}"),
        ("og:image", f"{SITE}/{rel_image}"),
        ("og:image:width", str(WIDTH)),
        ("og:image:height", str(HEIGHT)),
        ("og:image:alt", description),
        ("twitter:card", "summary_large_image"),
    ]


def main():
    tmp = tempfile.mkdtemp()
    try:
        shutil.rmtree(os.path.join(ROOT, "share"), ignore_errors=True)
        for kind in ("quotes", "poems"):
            os.makedirs(os.path.join(ROOT, "share", kind), exist_ok=True)

        for name in sorted(os.listdir(os.path.join(ROOT, "quotes"))):
            if not name.endswith(".html"):
                continue
            path = os.path.join(ROOT, "quotes", name)
            page = open(path, encoding="utf-8").read()
            body = re.search(r"<blockquote>\s*<p>(.*?)</p>", page, re.S).group(1)
            author = text(re.search(r'<span class="author">(.*?)</span>', page, re.S).group(1))
            quote_html = "<br>".join(l.strip() for l in body.split("<br>"))
            card = CARD.format(quote=quote_html, author=html.escape(author))
            image = f"share/quotes/{name[:-5]}.jpg"
            screenshot(tmp, card, os.path.join(ROOT, image))
            title = text(re.search(r"<title>(.*?)</title>", page, re.S).group(1))
            page = set_meta(page, tags_for(title, text(body), f"quotes/{name}", image))
            open(path, "w", encoding="utf-8").write(page)
            print("quote", name)

        for name in sorted(os.listdir(os.path.join(ROOT, "poems"))):
            if not name.endswith(".html"):
                continue
            path = os.path.join(ROOT, "poems", name)
            page = open(path, encoding="utf-8").read()
            image = f"share/poems/{name[:-5]}.jpg"
            frame = f'<iframe class="frame" scrolling="no" src="file://{html.escape(path)}"></iframe>'
            screenshot(tmp, frame, os.path.join(ROOT, image))
            title = text(re.search(r"<title>(.*?)</title>", page, re.S).group(1))
            description = re.search(r'<meta name="description" content="([^"]*)"', page).group(1)
            page = set_meta(page, tags_for(title, html.unescape(description), f"poems/{name}", image))
            open(path, "w", encoding="utf-8").write(page)
            print("poem", name)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
