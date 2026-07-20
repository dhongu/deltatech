- Features:

  - Display product page using internal code
  - Display product code in product page
  - Display product code in search results
  - Fast search when several product codes are pasted at once in the shop
    search box (finds any matching product instead of requiring all codes
    to match the same product)

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
