Loads product images from a web address instead of a file: paste the address of the image
(`https://...`) and Odoo downloads it.

- **Main product image**: The address pasted in **Image File Name** (product form, tab **Sales**)
  sets the product image; the field then keeps only the file name.
- **Extra images**: The address pasted in the **Image Name** of an extra image (**Ecommerce Media**)
  loads that image.
- **Import**: Updating existing products by import with the **Image File Name** column loads their
  images.
- **Safe download**: Only public `http`/`https` addresses are fetched, each redirect is checked, the
  answer must be an image of at most 10 MB, and only users allowed to edit products can trigger it.
