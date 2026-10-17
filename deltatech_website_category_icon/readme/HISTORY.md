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
