# /// script
# requires-python = ">=3.10"
# dependencies = ["requests", "beautifulsoup4", "markdownify", "pyyaml"]
# ///
"""Export the bakfiets.bike WordPress.com site into this Jekyll repo.

Usage: uv run scripts/export_wp.py

- Posts  -> _posts/YYYY-MM-DD-<slug>.md, permalink identical to WordPress.
- Pages  -> <slug>.md at the repo root, permalink identical to WordPress.
- Media  -> wp-content/uploads/YYYY/MM/<file>, the same paths WordPress served
            (and Google indexed), with GPS EXIF stripped (needs exiftool).

Safe to re-run: existing files are overwritten with the latest content.
"""

import html
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

import requests
import yaml
from bs4 import BeautifulSoup
from markdownify import markdownify

API = "https://public-api.wordpress.com/wp/v2/sites/bakfiet.wordpress.com"
SITE = "https://bakfiets.bike"
MEDIA_HOST = "https://bakfiet.wordpress.com"
ROOT = Path(__file__).resolve().parent.parent

# Jetpack blocks that only function on WordPress.com.
DROP_SELECTORS = [".wp-block-jetpack-subscriptions", ".wp-block-jetpack-contact-form", ".wp-block-spacer"]

session = requests.Session()


def fetch_all(endpoint, **params):
    items, page = [], 1
    while True:
        r = session.get(f"{API}/{endpoint}", params={"per_page": 100, "page": page, **params}, timeout=30)
        r.raise_for_status()
        items.extend(r.json())
        if page >= int(r.headers.get("X-WP-TotalPages", 1)):
            return items
        page += 1


def term_names(endpoint):
    return {t["id"]: html.unescape(t["name"]) for t in fetch_all(endpoint)}


def clean_text(s):
    return html.unescape(s).replace("\xa0", " ").strip()


def jekyll_date(local, gmt):
    """WordPress local time plus its UTC offset, e.g. 2023-11-17 19:05:31 -0800."""
    lt, gt = datetime.fromisoformat(local), datetime.fromisoformat(gmt)
    minutes = int((lt - gt).total_seconds() // 60)
    sign = "-" if minutes < 0 else "+"
    hh, mm = divmod(abs(minutes), 60)
    return f"{lt:%Y-%m-%d %H:%M:%S} {sign}{hh:02d}{mm:02d}"


def upload_path(url):
    """Map any WordPress media URL to its site path, e.g. /wp-content/uploads/2023/11/a.jpeg."""
    path = urlsplit(url).path
    if "/wp-content/uploads/" not in path:
        raise ValueError(f"not a WordPress upload: {url}")
    return path[path.index("/wp-content/uploads/"):]


def download(url):
    """Mirror a media file at its original path; returns the site path."""
    site_path = upload_path(url)
    dest = ROOT / site_path.lstrip("/")
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        r = session.get(MEDIA_HOST + site_path, timeout=60)
        r.raise_for_status()
        dest.write_bytes(r.content)
        if shutil.which("exiftool"):
            subprocess.run(["exiftool", "-q", "-overwrite_original", "-gps:all=", str(dest)], check=False)
        else:
            print(f"warning: exiftool not found, GPS data left in {dest}", file=sys.stderr)
        print(f"  media {site_path}")
    return site_path


def liquid_url(site_path):
    return "{{ '" + site_path + "' | relative_url }}"


def convert_body(rendered):
    soup = BeautifulSoup(rendered, "html.parser")
    for sel in DROP_SELECTORS:
        for el in soup.select(sel):
            el.decompose()
    # Flatten media-text blocks into image followed by text.
    for block in soup.select(".wp-block-media-text"):
        media = block.select_one(".wp-block-media-text__media")
        content = block.select_one(".wp-block-media-text__content")
        new = soup.new_tag("div")
        for part in (media, content):
            if part:
                new.append(part.extract())
        block.replace_with(new)
    for img in soup.find_all("img"):
        src = img.get("data-orig-file") or img["src"]
        img.attrs = {"src": liquid_url(download(src)), "alt": img.get("alt", "")}
    # Internal links become site-relative so they follow the Jekyll baseurl.
    for a in soup.find_all("a", href=True):
        if a["href"].startswith(SITE + "/"):
            a["href"] = liquid_url(a["href"][len(SITE):])
    md = markdownify(str(soup), heading_style="ATX", bullets="-")
    # Collapse the blank-line runs WordPress block markup leaves behind.
    out = []
    for line in (l.rstrip() for l in md.splitlines()):
        if line or (out and out[-1]):
            out.append(line)
    return "\n".join(out).strip() + "\n"


def featured_image(item):
    featured = item.get("_embedded", {}).get("wp:featuredmedia", [])
    if featured and featured[0].get("source_url"):
        return download(featured[0]["source_url"])
    return None


def write_markdown(dest, front, body):
    fm = yaml.safe_dump(front, sort_keys=False, allow_unicode=True, width=1000)
    dest.write_text(f"---\n{fm}---\n\n{body}", encoding="utf-8")
    print(f"wrote {dest.relative_to(ROOT)}")


def sitemap_media():
    """Images Google indexed via the WordPress sitemap, including ones not shown in post bodies."""
    r = session.get(f"{SITE}/sitemap.xml", timeout=30)
    r.raise_for_status()
    return re.findall(r"<image:loc>([^<]+)</image:loc>", r.text)


def main():
    categories = term_names("categories")
    tags = term_names("tags")
    (ROOT / "_posts").mkdir(exist_ok=True)

    posts = fetch_all("posts", _embed=1)
    for p in posts:
        path = urlsplit(p["link"]).path
        front = {
            "layout": "post",
            "title": clean_text(p["title"]["rendered"]),
            "date": jekyll_date(p["date"], p["date_gmt"]),
            "last_modified_at": jekyll_date(p["modified"], p["modified_gmt"]),
            "permalink": path,
            "categories": [categories[c] for c in p["categories"]],
            "tags": [tags[t] for t in p["tags"]],
            "description": clean_text(BeautifulSoup(p["excerpt"]["rendered"], "html.parser").get_text()),
            "wordpress_id": p["id"],
        }
        if image := featured_image(p):
            front["image"] = image
        write_markdown(ROOT / "_posts" / f"{p['date'][:10]}-{p['slug']}.md", front, convert_body(p["content"]["rendered"]))

    pages = fetch_all("pages", _embed=1)
    for p in pages:
        front = {
            "layout": "page",
            "title": clean_text(p["title"]["rendered"]),
            "permalink": urlsplit(p["link"]).path,
            "last_modified_at": jekyll_date(p["modified"], p["modified_gmt"]),
            "wordpress_id": p["id"],
        }
        if image := featured_image(p):
            front["image"] = image
        write_markdown(ROOT / f"{p['slug']}.md", front, convert_body(p["content"]["rendered"]))

    for url in sitemap_media():
        download(url)

    icon = session.get(f"https://public-api.wordpress.com/rest/v1.1/sites/bakfiet.wordpress.com?fields=icon", timeout=30).json()
    if icon.get("icon", {}).get("img"):
        download(icon["icon"]["img"])

    print(f"exported {len(posts)} posts, {len(pages)} pages")


if __name__ == "__main__":
    main()
