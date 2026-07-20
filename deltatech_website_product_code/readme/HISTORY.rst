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
