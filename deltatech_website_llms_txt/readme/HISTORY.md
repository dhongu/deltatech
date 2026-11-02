# History

## 19.0.1.1.0 (2026-11-02)

- The pages without a meta description in their SEO settings take the one set in their
  template (`<t t-set="website_meta_description">`), as the pages of a theme do: theme pages
  have no SEO field of their own, so they were listed without a description.
- The summary, the details and the custom file move from the settings to a new *llms.txt* tab
  of the website form (*Website > Configuration > Websites*), full width, for longer Markdown.
  The settings keep the *llms.txt* checkbox, with the links *Edit llms.txt* and *View llms.txt*.
- Romanian translation (`i18n/ro.po`).
- The *View llms.txt* link in the settings no longer logs the warning `"<a>" tag with "btn"
  class must have "button" role` at installation.

## 19.0.1.0.0 (2026-10-16)

- Initial release: `/llms.txt` generated per website from its pages, shop categories and
  company contact, with a summary, Markdown details or a fully custom file set in the settings.
