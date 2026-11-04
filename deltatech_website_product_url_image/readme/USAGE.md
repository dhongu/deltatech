1. Open the product (*Website > eCommerce > Products*), tab **eCommerce**. In the **Shop**
   group, paste the address of the image, starting with `https://`, in **Image File Name**.

   ![Product form, eCommerce tab: the image address typed in Image File Name (1); the product has no main image yet: Odoo shows the older grey image from Media in its place](static/description/en/01_adresa_imagine_produs.png)

2. Leave the field: Odoo downloads the image and sets it as the product image, and the field keeps only
   the file name. Save the product. If the address stays in the field, the image could not be loaded.

   ![The product image loaded from the address (1) and Image File Name reduced to lampa-led-10w.png (2)](static/description/en/02_imagine_incarcata_produs.png)

3. For an extra image of the product (**Media**), paste the address in its **Image Name** and
   leave the field: the image is downloaded in the same way. Press **Save** in the image window, then
   save the product.

   ![The extra image window over the product: Image Name (1) became the file name, the downloaded image (2) replaced the old one, and the Save button (3)](static/description/en/03_imagine_suplimentara_url.png)

4. Check the product page in the shop (**Go to Website**): the main image and the extra image come from
   the addresses.

   ![The product page in the shop: the first thumbnail is the main image and the second one, selected (1), is the extra image shown large](static/description/en/04_produs_magazin_imagine.png)

Updating existing products by import (with their ID column) loads the images too, when the
**Image File Name** column holds web addresses. Products created by the import keep the address as
text, without image.

Only public `http`/`https` addresses are fetched, the answer must be an image of at most 10 MB and only
users allowed to edit products can trigger the download.
