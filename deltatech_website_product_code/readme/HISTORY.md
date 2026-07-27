## 19.0.1.1.0 (2026-07-27)

- Optional exact-phrase search on the shop, new system parameter
  `website_search.exact_phrase` (default `False`). When enabled, the search
  term is matched as one single string instead of being split on spaces.
  Catalogues using OEM part numbers that contain spaces could not be searched
  by code: looking for `352 030 15 97` matched every product containing `352`
  or `030` or `15` or `97`, returning pages of results with the wanted product
  somewhere in the middle. If nothing matches the whole term, the search falls
  back to the per-term behaviour, so partial-word searches are unaffected.
  Ported from 18.0.1.3.0; uses `odoo.fields.Domain` instead of the deprecated
  `odoo.osv.expression` helpers.
- Tests for the exact-phrase search, including the fallback paths.
