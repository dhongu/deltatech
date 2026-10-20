Website Searchbar Optimization
===============================

This module reduces the number of autocomplete requests sent to `/website/snippet/autocomplete`
by applying two complementary optimizations to the website search bar widget.

Key Features
============

1.  **Increased Debounce Delay**:
    *   Increases the debounce delay from the default **400ms to 800ms**.
    *   The autocomplete request is triggered only after the user stops typing for 800ms, reducing unnecessary intermediate requests.

2.  **Minimum Search Term Length**:
    *   Adds a minimum term length check of **4 characters** before sending any request.
    *   If the search term (after trimming whitespace) is shorter than 4 characters, the autocomplete dropdown is cleared without making a server request.
    *   This prevents requests for very short, non-specific terms that would return too many results anyway.

How It Works
============

The module patches the standard `SearchBar` public interaction from `website` using Odoo's `patch()` mechanism:

*   In `setup()`, the `t-on-input` entry of `dynamicContent` is replaced with a debounced handler using the new 800ms delay.
*   In `onInput()`, a length check is performed before calling `fetch()`. Terms shorter than 4 characters trigger only a local `render()` call to clear the dropdown.

Usage
=====

Install the module and the optimizations are applied automatically to all website search bars.
No configuration is required. The constants `MIN_SEARCH_TERM_LENGTH` (4) and `DEBOUNCE_DELAY` (800ms)
can be adjusted directly in `static/src/js/searchbar.esm.js` if different values are needed.
