## 19.0.1.0.0 (2026-08-14)

- Migration to 19.0: the website search bar is no longer a `publicWidget` (`@website/snippets/s_searchbar/000`), it is the `SearchBar` public interaction (`@website/snippets/s_searchbar/search_bar`). The override was rewritten as a `patch()` on that interaction -- the debounce delay is now set on the `t-on-input` entry of `dynamicContent` in `setup()`, and the minimum term length is checked in `onInput()` against `this.inputEl.value` instead of the removed `this.$input`. Behaviour is unchanged: 800 ms debounce and no request under 4 characters.
