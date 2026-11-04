1. Open the product (*Website > eCommerce > Products*), tab **Sales**. In the **Ecommerce Shop**
   group, paste the address of the image, starting with `https://`, in **Image File Name**.

   ![Product form, Sales tab: the image address typed in Image File Name (1); the product has no image yet](static/description/en/01_adresa_imagine_produs.png)

2. Leave the field: Odoo downloads the image and sets it as the product image, and the field keeps only
   the file name. Save the product. If the address stays in the field, the image could not be loaded.

   ![The product image loaded from the address (1) and Image File Name reduced to lampa-led-10w.png (2)](static/description/en/02_imagine_incarcata_produs.png)

3. For an extra image of the product (**Ecommerce Media**), paste the address in its **Image Name** and
   leave the field: the image is downloaded in the same way.

   ![Extra product image: Image Name (1) became the file name and the downloaded image (2) replaced the old one](static/description/en/03_imagine_suplimentara_url.png)

4. Check the product page in the shop (**Go to Website**): the main image and the extra image come from
   the addresses.

   ![The product page in the shop with the main image and, on its left, the thumbnails with the extra image (1)](static/description/en/04_produs_magazin_imagine.png)

Updating existing products by import (with their ID column) loads the images too, when the
**Image File Name** column holds web addresses. Products created by the import keep the address as
text, without image.

Only public `http`/`https` addresses are fetched, the answer must be an image of at most 10 MB and only
users allowed to edit products can trigger the download.
