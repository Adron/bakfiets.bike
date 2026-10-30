# WordPress.com → GitHub Pages migration punch list

Goal: serve bakfiets.bike from this repo over HTTPS, with every existing URL still working.

## Content export
- [x] Export all posts (2) to `_posts/` with original dates, categories, tags, and descriptions
- [x] Export pages: `/about/`, `/centered-heading-with-contact-form/`
- [x] Mirror all media to its original `/wp-content/uploads/YYYY/MM/` paths (incl. 10 images indexed in the WP sitemap and the site icon)
- [x] Strip GPS EXIF data from the photos
- [x] Skip the 1 comment (spam) and the Jetpack subscribe/contact-form widgets
- [ ] Final re-export right before the DNS cutover, in case anything is published or edited on WordPress (`uv run scripts/export_wp.py`)
- [ ] Download the official WordPress.com export (Tools → Export → Export All: WXR + media zip) and keep it as a backup outside the repo

## URL / SEO preservation
- [x] Posts keep `/YYYY/MM/DD/slug/` (pinned via `permalink:` front matter; `_config.yml` uses the same pattern for new posts)
- [x] Timezone set to America/Los_Angeles so post dates in URLs match WordPress
- [x] Category (`/category/<slug>/`), tag (`/tag/<slug>/`), and year/month/day archive URLs regenerated with matching slugs
- [x] RSS kept at `/feed/` for existing subscribers; Atom at `/feed.xml`
- [x] `sitemap.xml` and `robots.txt` generated; canonical URLs and Open Graph tags point at `https://bakfiets.bike`
- [x] github.io preview is `noindex` so it can't compete with the real domain in search
- [x] Checked: every URL in the live WordPress sitemap (16) exists in the Jekyll build
- [ ] Not reproducible on GitHub Pages (low value, accepting the loss): `?p=ID` links, `wp.me` shortlinks, `/comments/feed/`, image resize URLs like `?w=1024` (the base file still loads; the parameter is ignored)

## GitHub Pages
- [ ] Merge the Jekyll site to `main`
- [ ] Enable Pages with source = GitHub Actions
- [ ] Confirm the workflow deploys and the preview renders at https://adron.github.io/bakfiets.bike/
- [ ] Review the preview: home, both posts, both pages, a category page, a tag page, `/feed/`

## Domain + HTTPS (needs WordPress.com and GitHub account access)
- [ ] Find where the domain is registered (DNS is on WordPress.com nameservers; likely registered through WordPress.com). Decide: keep the registration at WP.com and edit DNS there, or transfer the domain to another registrar
- [ ] Export the Jetpack subscriber list from WordPress.com (email subscribers won't carry over automatically)
- [ ] Verify the domain on GitHub: Settings → Pages → Add a domain → add the `_github-pages-challenge-adron` TXT record
- [ ] Lower the DNS TTL ahead of the cutover, if the DNS host allows it
- [ ] Cutover DNS:
  - [ ] Remove the WordPress A records `192.0.78.24` and `192.0.78.25`
  - [ ] Apex A: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
  - [ ] Apex AAAA: `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`
  - [ ] `www` CNAME → `adron.github.io`
- [ ] Repo Settings → Pages → Custom domain: `bakfiets.bike` (the next deploy then builds with an empty baseurl, so the preview's `noindex` drops off automatically)
- [ ] Wait for the DNS check and the Let's Encrypt certificate, then tick **Enforce HTTPS**
- [ ] Re-run the workflow after the custom domain is set (Actions → Deploy → Run workflow) so the build picks up the new base path

## After cutover
- [ ] Spot-check the post URLs, `/about/`, `/feed/`, a `/wp-content/uploads/...` image, and `http://` → `https://` and `www` → apex redirects
- [ ] Google Search Console: verify the domain (DNS TXT), submit `https://bakfiets.bike/sitemap.xml`, watch Coverage for 404s
- [ ] Contact page: replace the old WordPress form with a `mailto:` link or a form service (Formspree, etc.) if wanted
- [ ] Cancel the WordPress.com hosting plan only after the cutover is confirmed, and keep the domain registration renewing
