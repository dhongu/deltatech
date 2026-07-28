## 19.0.1.3.1 (2026-07-28)

- Exact-phrase search is now limited to terms carrying a digit. A term made of
  words alone is somebody describing a product, not quoting a code, and matching
  it as one string dropped the products whose words are spread out: on a live
  catalogue `Lant CLAAS` returned only the 24 products worded exactly that way,
  hiding `Lant combina agricola CLAAS` and the rest of the 145 that carry both
  words. Word-only searches are again matched per word, while codes - which
  contain digits, as `_looks_like_code()` already requires - keep the whole-term
  behaviour. Ported from 18.0.1.5.1.

## 19.0.1.3.0 (2026-07-28)

- Brought the search to parity with 18.0.1.5.0 by porting the three features
  that had been left on 18.0:
  - short search terms are dropped (`website_search.min_term_length`,
    default `3`), since they cannot use the trigram indexes and only force
    sequential scans;
  - a pasted list of product codes is resolved by looking for any of them
    instead of requiring one product to match them all
    (`website_search.multi_code_min_terms`, default `4`), searching one field
    at a time so every branch can use its own index;
  - while exact-phrase search is on, that list is only recognised when every
    term is long enough to be a code of its own
    (`website_search.standalone_code_min_length`, default `5`), so the groups
    of a spaced code such as `999 888 777 666` are never ORed together.
- All four parameters are editable from *Website > Configuration > Settings*.
- Domains are built with `odoo.fields.Domain` instead of the deprecated
  `odoo.osv.expression` helpers used on 18.0.

## 19.0.1.2.0 (2026-07-28)

- The exact-phrase search can now be switched on from *Website >
  Configuration > Settings*, in a **Product Search** block, instead of only
  through *Settings > Technical > System Parameters*. Ported from 18.0.1.5.0,
  which also exposes three numeric parameters that do not exist on this branch.

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
