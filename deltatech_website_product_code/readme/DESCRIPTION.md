- Features:

  - Display product page using internal code
  - Display product code in product page
  - Display product code in search results
  - Fast search when several product codes are pasted at once in the shop
    search box (finds any matching product instead of requiring all codes
    to match the same product)
  - Optional exact-phrase search, for catalogues whose codes contain
    spaces (OEM part numbers such as ``352 030 15 97``)

- Usage:

  - Use link: /shop/product-code/\<code\>

- Configuration (optional, System Parameters):

  - ``website_search.min_term_length`` (default ``3``): search terms
    shorter than this are ignored, since they cannot use the trigram
    indexes and only slow down the search.
  - ``website_search.multi_code_min_terms`` (default ``4``): minimum
    number of code-looking terms (e.g. ``AMAT1-12345``) pasted together
    before the fast multi-code search kicks in. Set to ``False`` or ``0``
    to disable it and fall back to the regular search.
  - ``website_search.exact_phrase`` (default ``False``): search the whole
    term as a single string instead of splitting it on spaces. Enable it
    for catalogues whose codes contain spaces, so that searching
    ``352 030 15 97`` returns the product with that code instead of every
    product containing ``352``, ``030``, ``15`` or ``97``. If no product
    matches the whole term, the regular per-term search is used as a
    fallback, so pasted code lists keep working.
