- Features:

  - Display product page using internal code
  - Display product code in product page
  - Display product code in search results
  - Optional exact-phrase search, for catalogues whose codes contain
    spaces (OEM part numbers such as ``352 030 15 97``)

- Usage:

  - Use link: /shop/product-code/\<code\>

- Configuration (Website > Configuration > Settings, *Product Search*):

  - ``website_search.exact_phrase`` (default ``False``): search the whole
    term as a single string instead of splitting it on spaces. Enable it
    for catalogues whose codes contain spaces, so that searching
    ``352 030 15 97`` returns the product with that code instead of every
    product containing ``352``, ``030``, ``15`` or ``97``. If no product
    matches the whole term, the regular per-term search is used as a
    fallback.
