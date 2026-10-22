Gives every eCommerce category its own **SVG icon** and shows it in the shop.

- New field **Icon (SVG)** on the eCommerce category, with a live preview on the
  category form.
- The categories shown on top of the shop (filmstrip) display the icon instead
  of the category image.
- The left category list shows a small icon before the category name.
- Option **Category Icons in List** (Website > Configuration > Settings, Shop -
  Products) decides which categories of the category list show an icon:
  - **Main categories only** (default): an opened branch lists its
    subcategories as plain text, which keeps the list light and easy to read;
  - **All categories**: every category with its own icon shows it;
  - **All categories, inherit from parent**: a subcategory without its own icon
    shows the icon of its closest parent that has one.
- Option **Category Icon Order** (same settings page) decides what the shop shows
  for a category, the first one found: **SVG, image, none** (default), **Image,
  SVG, none**, **SVG, image, first product image** or **Image, SVG, first product
  image**. *SVG* is the category's icon, else its closest parent's; *first
  product image* is the picture of the first published product of the category
  or its subcategories. The same order applies to the filmstrip, the left
  category list, the block Category Icon Grid and, when installed, the category
  menu and subcategory list of Website Shop Blocks.
- Website block **Category Icon Grid**, to drag on any page (home page, landing
  pages): the main categories or categories chosen by hand, with their icon and
  name, each linking to its shop page. The categories are rendered on each
  visit, so the page always shows the current icons; the maximum number and the
  icon size are options of the block. 6 columns on desktop, 2 on phones.
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
