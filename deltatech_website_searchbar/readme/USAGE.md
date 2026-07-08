Install the module and the optimizations are applied automatically to every website search bar — no configuration is required.

- The autocomplete request is now sent only after the visitor stops typing for **800 ms** (instead of the default 400 ms).
- No request is sent at all while the search term is shorter than **4 characters**; the dropdown is simply cleared locally.

If different values are needed, the constants `MIN_SEARCH_TERM_LENGTH` (4) and `DEBOUNCE_DELAY` (800) can be adjusted directly in `static/src/js/searchbar.esm.js`.
