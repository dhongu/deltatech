18.0.1.5.0 (2026-07-28)
~~~~~~~~~~~~~~~~~~~~~~~

**Added**

- The four search parameters are now editable from *Website > Configuration >
  Settings*, in a **Product Search** block, instead of only through
  *Settings > Technical > System Parameters*.
- The numeric ones are read and written explicitly rather than through the
  ``config_parameter`` shortcut, because core stores an integer ``0`` as
  ``False``, which deletes the parameter and restores the default. A shop that
  had switched the pasted-code fast path off with ``0`` would otherwise have it
  re-enabled by anyone opening the settings page and pressing Save.

18.0.1.4.0 (2026-07-28)
~~~~~~~~~~~~~~~~~~~~~~~

**Added**

- Exact-phrase search and the pasted-code-list fast path can now be used
  together. 18.0.1.3.1 disabled the fast path whenever
  ``website_search.exact_phrase`` was on, because the groups of a spaced code
  were mistaken for separate codes. The two are now told apart by the length of
  the terms: OEM part numbers are written in short groups
  (``366 200 05 01``, ``0798 318 0`` - one to four characters each), while a
  code that stands on its own is longer. New system parameter
  ``website_search.standalone_code_min_length`` (default ``5``, set to
  ``False``/``0`` to accept any length) controls the boundary; it only applies
  while exact-phrase search is on.
- Measured over the ~6 800 spaced codes of an agricultural-parts catalogue: no
  single code reached four groups of five characters or more, while the rows
  holding several codes on one line consistently did.

18.0.1.3.1 (2026-07-27)
~~~~~~~~~~~~~~~~~~~~~~~

**Fixed**

- Exact-phrase search no longer chains its fallback into the pasted-code-list
  fast path. A code whose groups each look like a standalone code, for example
  ``999 888 777 666``, was treated as four pasted codes when the whole term
  matched nothing, so the search returned every product containing any single
  group - measured at 472 results on a 10 000-product catalogue, where the
  per-term fallback returns none. In exact-phrase mode a term containing spaces
  is one code, so the OR expansion is now skipped and the search falls back to
  the per-term AND behaviour of the mixin. The fast path is unchanged when
  ``website_search.exact_phrase`` is off.

18.0.1.3.0 (2026-07-27)
~~~~~~~~~~~~~~~~~~~~~~~

**Added**

- Optional exact-phrase search on the shop, new system parameter
  ``website_search.exact_phrase`` (default ``False``). When enabled, the
  search term is matched as one single string instead of being split on
  spaces. Catalogues using OEM part numbers that contain spaces could not
  be searched by code: looking for ``352 030 15 97`` matched every product
  containing ``352`` or ``030`` or ``15`` or ``97``, returning pages of
  results with the wanted product somewhere in the middle. If nothing
  matches the whole term, the search falls back to the per-term behaviour,
  so pasted code lists and partial-word searches are unaffected.
- Tests for the exact-phrase search, including the fallback paths.

18.0.1.2.0 (2026-07-20)
~~~~~~~~~~~~~~~~~~~~~~~

**Added**

- Fast path for shop searches where several product codes are pasted
  together (e.g. copy-pasted from a parts list). The default search
  requires every pasted term to match the same product (AND), which
  always returned zero results for a list of different codes; this adds
  an OR-based search restricted to terms that look like product codes,
  new system parameter ``website_search.multi_code_min_terms``
  (default ``4``, set to ``False``/``0`` to disable).

18.0.1.1.0 (2026-06-02)
~~~~~~~~~~~~~~~~~~~~~~~

**Fixed**

- Ignore search terms shorter than ``website_search.min_term_length``
  (default ``3``) when searching products on the website. Short terms
  cannot use the trigram indexes and were forcing sequential scans,
  causing shop searches to take up to ~40s.

18.0.1.0.1 (2024-10-29)
~~~~~~~~~~~~~~~~~~~~~~~

- Migrated to 18.0.
