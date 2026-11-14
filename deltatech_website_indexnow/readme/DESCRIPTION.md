Tells the search engines of the [IndexNow](https://www.indexnow.org) protocol (Bing, Yandex,
Seznam, Naver) which pages of your Odoo website were published or changed, so that they crawl
them again in minutes instead of waiting for their next visit. Bing also feeds the web search of
ChatGPT and Copilot.

- **Key file served by Odoo**: The key that proves the site is yours is generated when IndexNow
  is enabled and served at `https://<your-domain>/<key>.txt`; a key you already have can be
  pasted instead.
- **Only what changed, every hour**: A scheduled action sends the published pages changed since
  its last run, including the content edited in the website builder, and the published products,
  blog posts, events, jobs and courses of the installed apps.
- **Everything, on demand**: *Send all pages now* sends every published page once, after the
  first setup or a large change.
- **Result at a glance**: The settings show the time and result of the last submission, with a
  clear message when the key file is not found or the URLs do not belong to the domain.
- **One key per website**: On a multi-website database each domain has its own key and sends
  only its own pages.

Google does not use IndexNow: keep submitting the sitemap in Google Search Console.

**Data sent:** only the addresses of pages that are already public, the domain and the key.
