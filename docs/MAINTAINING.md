# Maintaining Budihal logs

## Architecture and preserved content

The repository began with locally vendored Beautiful Jekyll 6.0.1 (not a remote theme), Bootstrap/jQuery/CDN fonts, a custom blog RSS feed, and `jekyll-paginate` / `jekyll-sitemap`. The old CI workflow built and uploaded a Pages artifact but had no deployment job. Repository files cannot establish the live repository's Pages settings or custom-domain configuration; check those settings before publishing.

The redesign keeps Jekyll, Liquid, Kramdown/Rouge, the existing gemspec/dependencies, all original articles/assets, `/aboutme`, `/tags`, `/404.html`, `/feed.xml`, and `/:year-:month-:day-:title/` post permalinks. The existing article has no front matter, which Jekyll accepts with defaults; its metadata is provided in `_config.yml` without touching its text. The pre-existing uncommitted article edit was left intact.

Active layouts use only local CSS and vanilla JS, with no external fonts, trackers, Bootstrap, or jQuery. Legacy theme files remain available but are not loaded. Pagination is replaced by a full chronological archive. Configured comments remain supported on articles. Set `toc: true` for a lightweight, progressively enhanced article contents menu.

No prior `url`, `baseurl`, or CNAME was present. Local defaults now reflect this repository's GitHub project-site address. The Pages Action overrides `url` and `baseurl` using `actions/configure-pages` (including custom domains); any custom domain must remain configured in GitHub Settings → Pages. The article layout rebases original `/assets/` references without changing Markdown. For new Markdown, prefer Liquid `relative_url` rather than hardcoded root paths.

## Editing the homepage and site

- `_data/home.yml`: the two introduction paragraphs.
- `_includes/figlet.html`: pre-generated FIGlet `banner` art, slanted and converted to checkerboard Braille dots to match the reference style, with a separate accessible H1. No browser font-art generator or runtime dependency is required.
- `_config.yml`: title, description, navigation, verified social/contact links, permalink rules.
- `assets/css/site.css`: palette variables and all responsive/editorial styles. The specified muted colour is used decoratively; small metadata uses a darker secondary text colour in light mode for readable contrast.
- Theme selection follows the OS unless manually selected. The `budihal-theme` localStorage key saves the override; removing it restores system following. A tiny head script applies it before CSS loads. Without JS the OS palette still works, all content is readable, and inactive filter controls stay hidden.

## Add a blog post

Create `_posts/YYYY-MM-DD-your-slug.md`:

```yaml
---
layout: post
title: "Your article title"
date: 2026-11-07
tags: [systems, rust]
description: "A short plain-text introduction."
toc: true
---
```

Write Markdown underneath. Images: `![Description]({{ '/assets/img/example.png' | relative_url }})`. Both `/` and `/blogs/` use `_includes/blog-list.html`; no second list needs editing. Dates sort newest first, reading time is estimated at 220 words/minute, and the RSS URL remains `/feed.xml`. Multiple checked tags match **any** selected tag; clear selection restores all entries. Numbering reflects archive position and stays stable while filtering.

Builds retain the original workflow's `--future` behavior, so future-dated posts are published too. Remove `--future` from local/Actions commands if you want date-based scheduling instead.

## Add a Cool Stuff entry

Create `_cool_stuff/unique-slug.md` (create the directory for your first entry):

```yaml
---
title: "A paper worth revisiting"
date: 2026-11-07
tags: [databases, papers]
link: "https://example.com/paper"
---

Your own notes, with **Markdown** formatting.
```

`link` is optional. Use `link` rather than `url` from the task's illustrative schema: Jekyll reserves `url` for the generated document path, so it does not expose that front-matter value reliably without a custom plugin. Without an external URL it is a text observation. Filenames provide permanent journal anchors, so keep them stable. Entries are grouped by month, newest first; filtering hides empty month groups. Collection entries appear inline, not on additional individual pages. Feed: `/cool-stuff/feed.xml` (links point to permanent journal anchors).

## Music and Now

- `_data/music.yml`: add items to `favourites` with `name`, optional `year`, `artwork` (local path or HTTPS URL), and optional `link`. Personal notes and empty-shelf descriptions are no longer displayed.
- `_music_notes/` remains available for existing Markdown, but the Music Notes section is no longer displayed on `/music/`. The Music page has no visible introductory description; recent listening is text-only.
- `now.md`: edit the Reading / Building / Learning / Listening sections. All initial entries are explicitly unfilled, not claims about current activities.
- `aboutme.md` remains your original biography. `contact.html` reads existing verified links from `_config.yml`, including email, GitHub, LinkedIn, Twitter/X, WhatsApp, and Medium. It does not use a form.

## Last.fm: credentials stay out of the site

1. Obtain a Last.fm API key at <https://www.last.fm/api/account/create>.
2. In repository Settings → Secrets and variables → Actions, add:
   - **Secret** `LASTFM_API_KEY`.
   - **Repository variable** `LASTFM_USERNAME` (your Last.fm username; not a secret).
3. Enable Actions and run **Build and deploy Budihal logs** manually once.
4. Verify the deployed `/assets/data/lastfm.json` contains your tracks and no credentials.

`scripts/fetch_lastfm.py` calls `user.getRecentTracks` once per production build, keeps only eight tracks and safe public metadata, and writes the snapshot **before** Jekyll builds. The Pages artifact includes that generated file. An Actions cache retains the last successful snapshot between builds; it is not committed to the repository. API errors retain cached data. Without credentials/data, both widgets retain their static fallback. Public listening history, track URLs, and optional artwork URLs are published, but never the API key or username config.

The schedule runs twice hourly (48 requests/day), with no browser polling or browser Last.fm API calls. GitHub may delay schedules and disables schedules on inactive public repositories after 60 days; you can run the workflow manually. Adjust/remove the cron if this cadence is unnecessary. Recent listening on the Music page is text-only; returned artwork URLs are not loaded by that widget.

This is a **snapshot, not a live presence indicator**. `♫` appears only when the API marked the first track as playing and the snapshot is less than ten minutes old. Older snapshots still show the last known track, without claiming it is live. No client API key, proxy, server process, or streaming embed is required. Do not put a key in YAML, browser JS, or committed JSON.

## Deployment and permissions

Set **Settings → Pages → Build and deployment → Source: GitHub Actions**. The new workflow explicitly builds and deploys the artifact; do not also run a competing native/branch deployment. Production deploys only from the repository's default branch, including scheduled/manual runs; PRs and other branches build/test without deploying or receiving Last.fm credentials.

Permissions:

- Workflow/build: `contents: read`; build also uses `pages: read` to discover the configured Pages URL.
- Deployment job: `pages: write`, `id-token: write`.
- GitHub environment: `github-pages`; approve it if environment protection rules require approval.
- No `contents: write`, personal access token, or cache-commit bot is needed.

The workflow uses Ruby 3.3, the existing Gemfile/gemspec, and committed `Gemfile.lock`. No custom Jekyll plugin or Node build is required. Config files are merged `_config.yml,_config_pages.yml`, so actual Pages domain/base path wins (the old workflow used the reverse precedence).

## Local development and checks

Use Ruby 3.3, Bundler, and Python 3. On Linux, building Ruby/native gems may require a compiler and development headers for OpenSSL, zlib, libyaml, and libffi.

```sh
bundle install
bundle exec jekyll serve --future
# Open http://127.0.0.1:4000/budihal_logs.github.io/
```

```sh
bundle exec jekyll build --future --strict_front_matter
python3 scripts/check_site.py _site /budihal_logs.github.io
python3 -m unittest discover -s tests -p 'test_*.py'
node --check assets/js/site.js  # optional; Node is not needed to build
```

The Python suite builds isolated unpublished fixture collections in both root-domain and project-site configurations, tests collection feeds/Markdown/order, and tests Last.fm normalization, absent credentials, and network failure. The site checker verifies internal links/assets/anchors, navigation pages, the original article URL, canonical presence, both RSS feeds, sitemap, and JSON output.

Optional real browser checks (Node only for testing, no package files added to the site):

```sh
npm install --prefix /tmp/budihal-browser playwright
NODE_PATH=/tmp/budihal-browser/node_modules /tmp/budihal-browser/node_modules/.bin/playwright install chromium
# Keep jekyll serve running in a second terminal:
NODE_PATH=/tmp/budihal-browser/node_modules node tests/browser.cjs
# Set CHROMIUM_PATH=/path/to/chromium to reuse an installed browser.
# SITE_URL may override the preview address.
```

## Verification and remaining manual steps

Verified locally: strict Jekyll build, root/project-site fixture builds, generated internal links/assets/anchors and feeds, unchanged article content, real Chromium rendering at 320/375/768/1280px, theme persistence/system changes, multi-tag/keyboard filtering and clearing, no-result state, cached Last.fm success/staleness/failure fixtures, missing artwork, article images/TOC, and no-JS archive reading. Desktop/mobile screenshots were visually inspected. No browser runtime errors occurred in those checks.

Still requires your repository/account: selecting the Actions deployment source, supplying Last.fm credentials, verifying a real API response and actual GitHub Pages deployment/custom domain. No live credentials were available during implementation. Screen-reader behavior, Safari/Firefox, and the repository's environment protection rules should receive a manual check before announcing the redesign.
