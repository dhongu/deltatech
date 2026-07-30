# History

## 19.0.1.0.0 (2026-07-30)

- Initial release. Shop listing pages beyond the last real one now return
  `404` instead of being silently clamped to the last page by
  `portal.controllers.portal.pager`, which made every `/shop/page/N` answer
  `200` with duplicate content and left crawlers walking the page number
  upwards without end.
