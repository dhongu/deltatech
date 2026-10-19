## 19.0.1.3.0 (2026-10-19)

- New website block **Category Icon Grid** (Catalog group of the editor): a grid
  of eCommerce categories with their icon and name, each linking to its shop
  page. Options: main categories or categories chosen by hand (kept in the
  chosen order), maximum number (1 to 48) and icon size. The page keeps only
  the options; the categories are rendered by the server on each visit, for
  the current website, so the block follows the icons of the database.
  Categories without an icon show only their name. 6 columns on desktop, 3 on
  tablets and 2 on phones.

## 19.0.1.2.0 (2026-10-17)

- The Boolean **Inherit Category Icons** becomes the choice **Category Icons in
  List**: main categories only (new default, as on agrotrac.ro: an opened
  branch stays plain text and the page light), all categories, or all
  categories with the parent's icon as fallback. A website that had the
  Boolean set gets the last choice (migration).
- Categories on top of the shop (filmstrip) without their own icon or image now
  show their closest parent's icon instead of the empty placeholder.

## 19.0.1.1.0 (2026-10-17)

- New website option **Inherit Category Icons**: in the category list, a
  subcategory without its own icon shows the icon of its closest parent that
  has one (new computed field `icon_inherited_html`).
- `currentColor` icons are documented and tested: they take the color of the
  category link.

## 19.0.1.0.1 (2026-10-17)

- The icon and the name in the category list now sit in an inner flex span,
  instead of making the link itself a flex box. Themes that restyle the link
  (Agroamat forces `display: block !important` on it) no longer push a long
  name's second line under the icon.

## 19.0.1.0.0 (2026-10-17)

- First release: SVG icon on eCommerce categories, checked against an
  allow-list when saved, shown in the left category list and in the categories
  filmstrip.
