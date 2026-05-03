# Site Maintenance

This file is a quick reference for common MENACOSE website maintenance tasks.

## Logo

### Change the logo image

1. Put the new logo file in `assets/images/`
2. Update these values in `_config.yml` if the filename changed:

```yml
logo: "/assets/images/logo.png"
logo_icon: "/assets/images/logo.png"
```

Files that use the logo:

- `_includes/header.html`
- `_includes/header_2.html`
- `_includes/footer.html`

### Change the logo size

Logo sizing is controlled in:

- `assets/scss/templates/_menu.scss`

Current rules:

```scss
.site-logo {
  max-height: 64px;
  width: auto;
}

.site-logo-footer {
  max-height: 84px;
}
```

Mobile sizes are also defined in the same file:

```scss
@include mobile {
  .site-logo {
    max-height: 52px;
  }
}

@include mobile-xs {
  .site-logo {
    max-height: 48px;
  }
}
```

Guideline:

- Increase `max-height` to make the logo bigger
- Decrease `max-height` to make the logo smaller
- Keep `width: auto` so the aspect ratio stays correct

## Favicon

Favicon files:

- `assets/images/favicon.png`
- `assets/images/favicon.ico`

Referenced in:

- `_includes/head.html`

If you replace the favicon with a different filename, update the paths in `_includes/head.html`.

## Event Calendar Sync

The website calendar entries are managed in:

- `_data/homepage.yml`

Automatic Outlook sync is handled by:

- `.github/workflows/sync-calendar.yml`
- `scripts/sync_outlook_calendar.py`

Generated Outlook event pages are written into:

- `_posts/`

Important:

- Outlook-generated posts contain `sync_source: outlook`
- Manual event posts should not contain that field
- Manual `events:` entries in `_data/homepage.yml` can be overwritten by the sync workflow

## Event Post Pages

Manual event posts live in:

- `_posts/`

Example:

- `_posts/2026-02-15-Sub-Chapter-FrameworkWG.md`

To create a manual event page:

1. Add a new file in `_posts/`
2. Use the filename pattern:

```text
YYYY-MM-DD-your-event-name.md
```

3. Use front matter like:

```yml
---
layout: event
title: "Event Title"
date: 2026-05-03
tags: events
categories: [events]
author: "Your Name"
featured: true
---
```

## Local Build Check

To test the site locally:

```bash
bundle exec jekyll build
```

If that succeeds, the site should usually be safe to push.

## Recommended Workflow

For content/layout changes:

```bash
git status
git add <files>
git commit -m "Describe the change"
git push origin main
```

For Outlook calendar updates:

1. Create or update the event in Outlook
2. Wait for the GitHub Action to sync it, or run the workflow manually
3. Confirm `_data/homepage.yml` and the generated `_posts/` page were updated

