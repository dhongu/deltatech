# History

## 19.0.1.1.0 (2026-11-02)

- The pages without a meta description in their SEO settings take the one set in their
  template (`<t t-set="website_meta_description">`), as the pages of a theme do: theme pages
  have no SEO field of their own, so they were listed without a description.

## 19.0.1.0.0 (2026-10-16)

- Initial release: `/llms.txt` generated per website from its pages, shop categories and
  company contact, with a summary, Markdown details or a fully custom file set in the settings.
