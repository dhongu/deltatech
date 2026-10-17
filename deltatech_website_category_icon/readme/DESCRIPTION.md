Gives every eCommerce category its own **SVG icon** and shows it in the shop.

- New field **Icon (SVG)** on the eCommerce category, with a live preview on the
  category form.
- The categories shown on top of the shop (filmstrip) display the icon instead
  of the category image.
- The left category list shows a small icon before the name of each category
  that has one (view **Category Icons in List**, can be archived).
- Option **Inherit Category Icons** (Website > Configuration > Settings, Shop -
  Products): in the category list, a subcategory without its own icon shows the
  icon of its closest parent that has one, so a large tree needs icons only on
  its main branches.
- Icons drawn with `currentColor` take the color of the category link, so they
  follow the theme, the hover color and the active category.
- The icon is checked when saved, so it is safe to show on public pages: only
  flat shapes are accepted (`path`, `rect`, `circle`, `ellipse`, `line`,
  `polyline`, `polygon`, `g`), with colors, numbers and `transform`. Scripts,
  styles, links, external images and event handlers are refused with a message
  that says what to fix. The drawing needs a `viewBox`; its size comes from the
  page.

The icons can be drawn by hand, generated in bulk by Terrabit in the style of
your shop, or written by any tool through the `icon_svg` field (import, XML-RPC).
