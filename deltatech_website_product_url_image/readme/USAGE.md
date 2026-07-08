1. Open a product (**Website > eCommerce > Products**, or **Sales > Products**) and go to the extra info section of the product form.
2. In the **Image File Name** field, paste the full URL of an image (must start with `http://` or `https://`), then leave the field (trigger the onchange).
3. Odoo downloads the image from that URL and sets it as the product's main image; the field is then reduced to just the file name (e.g. `photo.jpg`) as a record of where it came from.
4. The same behavior applies to each entry in the product's **Extra Product Media** (product.image) list: type/paste an image URL into the **Name** field of an image line and it is downloaded and used as that image.
