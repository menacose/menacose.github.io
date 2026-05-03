# Dizer Jekyll

Dizer Jekyll Creative Template ported from [Dizer HTML Template](https://themefisher.com/products/dizer/)

![dizer-jekyll](https://demo.themefisher.com/thumbnails/dizer.png)

[Live Preview](http://demo.themefisher.com/dizer-jekyll/)

## Setup

To start your project, fork this repository
After forking the repo, your site will be live immediately on your personal Github Pages account, e.g. `https://yourusername.github.io/your-repo-name/`.

Make sure GitHub Pages is enabled for your repo. It might take some time for the site to propagate entirely.

## Customize

Things you can customize in `_data/settings.yml` (no HTML/CSS):

- Theme General Settings ( name, logo, email, phone, address )
- Hero Section
- About Section
- Team Section
- Experience Section
- Education Section
- Services Section
- Portfolio Section
- Testimonials Section
- Client Slider Section
- Contact Section

## Deployment

To run the theme locally, navigate to the theme directory and run `bundle install` to install the dependencies, then run `jekyll serve` or `bundle exec jekyll serve` to start the Jekyll server.
I would recommend checking the [Deployment Methods](https://jekyllrb.com/docs/deployment-methods/) page on Jekyll's website.

## Calendar Sync

The website calendar at `/events/calendar` reads from `_data/homepage.yml` under `events`. That section is now meant to be updated automatically from Outlook by the GitHub Actions workflow in `.github/workflows/sync-calendar.yml`.

### One-time setup

1. In Outlook, publish the calendar you want the website to follow and copy its public `.ics` URL.
2. In GitHub, open `menacose/menacose.github.io` and add a repository secret named `OUTLOOK_CALENDAR_ICS_URL`.
3. Set that secret value to the published Outlook `.ics` URL.
4. In GitHub Actions, run the `Sync Outlook Calendar` workflow once manually to verify the first import.

### Day-to-day operation

After setup, the repo updates automatically:

- You create or update the invitation in Outlook.
- Outlook publishes the change in the `.ics` feed.
- GitHub Actions fetches that feed automatically every 10 minutes at `07, 17, 27, 37, 47, 57` minutes past the hour in UTC.
- The workflow rewrites the `events:` section in `_data/homepage.yml`, generates synced event pages directly in `_posts`, commits the changes, and pushes them.
- GitHub Pages rebuilds the live website from the updated repo.

### Important note

After this is enabled, the `events:` list in `_data/homepage.yml` becomes workflow-managed. If you want an event to stay on the website, it should exist in the Outlook calendar that is being published and synced.

By default, the sync script does not overwrite `events:` with an empty list. If the Outlook feed is empty, the workflow keeps the existing entries unchanged. To intentionally clear the website events from Outlook, set `CALENDAR_ALLOW_EMPTY_SYNC` to `true` in the workflow file.

Generated event pages intentionally strip meeting URLs from the invitation body before writing the page content. Calendar entries link to the generated internal event page, not directly to the meeting link.

## Reporting Issues

We use GitHub Issues as the official bug tracker for the **Kross Theme**. Please Search [existing issues](https://github.com/themefisher/dizer-jekyll/issues). It’s possible someone has already reported the same problem.
If your problem or idea is not addressed yet, [open a new issue](https://github.com/themefisher/dizer-jekyll/issues/new)

## Technical Support or Questions

If you have questions or need help integrating the product please [contact us](mailto:themefisher@gmail.com) instead of opening an issue.

<!-- licence -->
## License

Copyright (c) 2016 - Present, Designed & Developed by [Themefisher](https://themefisher.com)

**Code License:** Released under the [MIT](https://github.com/themefisher/dizer-jekyll/blob/main/LICENSE) license.

**Image license:** The images are only for demonstration purposes. They have their license, we don't have permission to share those images.
