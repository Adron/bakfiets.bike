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

## Theme

The look recreates the WordPress.com **Fewer** theme the site used on WordPress: Epilogue (self-hosted
in `assets/fonts/`), the off-white palette, and the 1/3 + 2/3 column layouts. It lives in
`_layouts/`, `_includes/`, and `assets/css/fewer.css`, with no theme gem. The home page intro
text is in `index.md`.

For an image beside text, like the WordPress media-and-text block, use:

```html
<div class="wp-block-media-text is-stacked-on-mobile" style="grid-template-columns:25% auto">
<figure class="wp-block-media-text__media"><img src="{{ '/wp-content/uploads/2026/10/photo.jpeg' | relative_url }}" alt=""></figure>
<div class="wp-block-media-text__content" markdown="1">

Markdown text here.

</div>
</div>
```

Add `has-media-on-the-right` (and put the text `div` first) to flip it. Set `sticky: true` in a
post's front matter to pin it first on the home page.

## Local preview

```sh
bundle install
bundle exec jekyll serve   # http://127.0.0.1:4000
```

## Re-importing from WordPress

While WordPress.com is still live, `uv run scripts/export_wp.py` refreshes `_posts/`, the page
files, and `wp-content/uploads/` from the WordPress.com API.
