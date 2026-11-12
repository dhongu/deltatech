Product feeds and other sales channels often need a short product text next to the full website description. This module adds a translatable short description to the product and two ways to publish products on the website.

- **Short description**: Each product gets a *Website short description*, an HTML editor on the sales page of the product form. The text is translatable per language.
- **Both texts together**: The product's *Website description* is shown beside it in the same place, so both texts are edited together.
- **Publish button**: A *Publish* button in the button box of the product form publishes the product on the website.
- **Bulk publish**: The *Publish on Website* action in the product list publishes the selected products that are not published yet and leaves the others unchanged.

The module depends on `website_sale_stock` and has no security groups of its own. It only stores the short description; other Terrabit modules, such as *Products Feed* (`deltatech_feed`), read it.
