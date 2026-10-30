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

## Theme
- [x] Identified the WordPress theme: Fewer (WordPress.com block theme by Automattic)
- [x] Recreated it in Jekyll (layouts, includes, `assets/css/fewer.css`) and dropped Minima
- [x] Self-hosted the Epilogue font (SIL OFL) instead of loading it from WordPress.com
- [x] Home page: intro column (text ported from the WP template) + 2-up post grid, with the sticky post first
- [x] Post page: categories/byline column, large title, excerpt lead-in, tags footer
- [x] Image-beside-text (media & text) blocks kept with their original column widths
- [x] Page, category/tag/date archive layouts match WordPress
- [x] Checked against the live site at 1440px: post header, excerpt, and first media block positions match to the pixel; stacks for mobile like Fewer
- [x] Jetpack email "Subscribe" button replaced with "Subscribe via RSS" (to `/feed/`)
- [ ] Not carried over (WordPress/Jetpack-only): share buttons, likes, comment form, the mobile hamburger menu (the nav wraps instead), and the footer's "…" placeholder columns
- [ ] Optional: re-add email subscriptions via a newsletter service if the Jetpack subscribers should keep getting posts

## GitHub Pages
- [ ] Merge the Jekyll site to `main`
- [ ] Enable Pages with source = GitHub Actions
- [ ] Confirm the workflow deploys and the preview renders at https://adron.github.io/bakfiets.bike/
- [ ] Review the preview: home, both posts, both pages, a category page, a tag page, `/feed/`

## Domain + HTTPS: WordPress.com DNS → Route 53 → GitHub Pages

Facts (checked 2026-10-30): registrar is Automattic (WordPress.com), and the registration runs to 2027-11-19.
DNSSEC is off, so the nameserver switch is safe. The `.bike` delegation TTL is 1h. No MX or email records.

### Phase 1: Route 53 zone mirrors WordPress (no visible change)
- [x] Hosted zone `bakfiets.bike` created: `Z083035615ECSAEEABKSY` (AWS account 196936048600)
- [x] Mirrored records: apex A `192.0.78.24`, `192.0.78.25` (TTL 300); `www` CNAME → `bakfiets.bike` (TTL 300)
- [x] Verified the Route 53 nameservers answer identically to `ns1.wordpress.com`
- [x] Skipped `_domainconnect` TXT (WordPress.com-only helper)

### Phase 2: switch nameservers at WordPress.com (no downtime: both sides serve the same answers)
- [x] WordPress.com → Upgrades → Domains → bakfiets.bike → Name servers → "Use custom name servers" (saved 2026-10-30 15:02 PT):
  - `ns-138.awsdns-17.com`
  - `ns-593.awsdns-10.net`
  - `ns-1387.awsdns-45.org`
  - `ns-1563.awsdns-03.co.uk`
- [x] Keep everything else on WordPress as is: the site, the plan, the domain connection, and auto-renew. WordPress.com keeps serving the site because the A records still point at it.
- [x] Registry delegated to Route 53 at 15:17 PT; 1.1.1.1, 8.8.8.8, and 9.9.9.9 all return the Route 53 answers, and the WordPress site still serves (200)

### Phase 3: verify the domain with GitHub (any time in Phase 1 or 2)
- [x] github.com/settings/pages → Add a domain → `bakfiets.bike` (pending verification)
- [x] TXT `_github-pages-challenge-adron.bakfiets.bike` added to Route 53
- [x] Domain verified on GitHub (github.com/settings/pages shows bakfiets.bike Verified)

### Phase 4: cutover to GitHub Pages (pick a quiet time)
- [ ] Repo Settings → Pages → Custom domain `bakfiets.bike` (or `gh api -X PUT repos/Adron/bakfiets.bike/pages -f cname=bakfiets.bike`)
- [ ] Re-run the Pages workflow so it builds with an empty base path (this also drops the preview `noindex`)
- [ ] Route 53 UPSERT, TTL 300:
  - Apex A: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
  - Apex AAAA: `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`
  - `www` CNAME → `adron.github.io`
- [ ] Wait for GitHub's Let's Encrypt certificate (usually 5–30 min), then tick **Enforce HTTPS**
  - The only unavoidable gap is between DNS reaching GitHub and that certificate being issued. WordPress sends HSTS, so returning visitors get a certificate error, not a plain-HTTP fallback, during those minutes.
  - Rollback: UPSERT the A records back to `192.0.78.24/25` and the `www` CNAME back to `bakfiets.bike`; it takes effect within 5 minutes.
- [ ] After it's stable: CAA `0 issue "letsencrypt.org"` and raise TTLs to 3600

## After cutover
- [ ] Optional: Route 53 query logging (CloudWatch Logs in us-east-1, KMS-encrypted) and DNSSEC signing for the zone
- [ ] Optional: transfer the registration to Route 53 Domains ($43, adds a year). Unlock it and get the auth code at WordPress.com first.
- [ ] Don't cancel the WordPress.com plan, remove the domain from the site, or turn off auto-renew until GitHub has served the site cleanly for a while. Then make the WordPress site private (Settings → Privacy) so `bakfiet.wordpress.com` can't serve a duplicate copy.
- [ ] Spot-check the post URLs, `/about/`, `/feed/`, a `/wp-content/uploads/...` image, and `http://` → `https://` and `www` → apex redirects
- [ ] Google Search Console: verify the domain (DNS TXT), submit `https://bakfiets.bike/sitemap.xml`, watch Coverage for 404s
- [ ] Contact page: replace the old WordPress form with a `mailto:` link or a form service (Formspree, etc.) if wanted
