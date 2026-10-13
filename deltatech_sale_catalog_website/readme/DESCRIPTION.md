Sale Catalog Website Categories & Image Zoom
============================================

This module improves the **product catalog opened from a Sales Order** (the
"Catalog" button on a quotation / sales order). The changes apply **only to the
Sales catalog** — the Purchase catalog keeps the standard behaviour.

Key Features:
-------------

- **Website categories in the left panel**: the search panel shows the *website*
  categories (`public_categ_ids`) as a hierarchical tree instead of the internal
  product categories. Selecting a parent category also lists the products of its
  sub-categories (cascading filter).
- **Full-size product image on click**: clicking a product image in the catalog
  opens it at full resolution in a dialog, so you can inspect the product while
  adding it to the order.

Technical notes:
----------------

- The Sales catalog kanban and search views are swapped only for
  ``sale.order.action_add_from_catalog``; the shared native views are left
  untouched, so Purchase is not affected.
- The website-category tree is powered by a dedicated ``search_panel_select_range``
  implementation on ``product.product`` (the many2many ``public_categ_ids`` is not
  supported by the generic category range) together with a ``SearchModel`` that
  applies the ``child_of`` operator so the hierarchy cascades.
