# Bakfiets.bike

Source for [bakfiets.bike](https://bakfiets.bike), a Jekyll site deployed to GitHub Pages by
`.github/workflows/pages.yml` on every push to `main`. It was migrated from WordPress.com; see
[punch-list.md](punch-list.md) for migration status.

## Writing a post

Add `_posts/YYYY-MM-DD-your-slug.md`:

```markdown
---
title: Your title
categories: [Meetup]
tags: [cargo bike]
description: One or two sentences for search results and social cards.
image: /wp-content/uploads/2026/10/photo.jpeg   # optional social/featured image
---

Body in Markdown. Images: ![alt]({{ '/wp-content/uploads/2026/10/photo.jpeg' | relative_url }})
```

It publishes at `/YYYY/MM/DD/your-slug/`, the same URL scheme WordPress used. Don't change a
published post's filename or date, because that changes its URL. Category and tag pages
(`/category/<name>/`, `/tag/<name>/`) and the date archives are generated automatically.

Put images under `wp-content/uploads/YYYY/MM/` and strip location data first:
`exiftool -overwrite_original -gps:all= photo.jpeg`.

## Local preview

```sh
bundle install
bundle exec jekyll serve   # http://127.0.0.1:4000
```

## Re-importing from WordPress

While WordPress.com is still live, `uv run scripts/export_wp.py` refreshes `_posts/`, the page
files, and `wp-content/uploads/` from the WordPress.com API.
