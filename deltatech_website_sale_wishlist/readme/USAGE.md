1. Go to *Website > eCommerce > Products > Wishlists*. The list shows every product your customers
   added to their wishlist, on all websites: the customer (*Owner*), the product, its
   *Quantity On Hand* and the price when it was added. *Quantity On Hand* is the stock of the
   warehouses of the companies selected in the company switcher. A product wished by several customers shows
   on one line per customer.

   ![The Wishlists list under the eCommerce menu: columns Owner, Product, Quantity On Hand and Price; Lampă de birou LED is wished by three customers with 0.00 on hand, Scaun de birou ergonomic has 12.00 and Birou reglabil electric 2.00](static/description/en/01_lista_favorite.png)

2. Click a line to open it. The form shows the same data. *Quantity On Hand* is computed each time
   it is displayed; it is not stored on the line.

   ![The form of the wishlist line Ana Popescu - Lampă de birou LED: Owner Ana Popescu, Product Lampă de birou LED, Quantity On Hand 0.00 highlighted and Price 149.00](static/description/en/02_formular_favorit.png)

3. Back in the list, select the lines of the products you want to bring in stock and click
   *Replenish*. For **each selected line**, the module procures **one unit** of the product in the
   stock location of the user's default warehouse, following the product route: a request for
   quotation with *Buy* (needs a vendor on the product) or a manufacturing order with
   *Manufacture*. If one selected product has no such route, Odoo shows an error and nothing is
   created for any selected line. A product with the *Buy* route but no vendor gets no request for
   quotation, without any message.

   ![The Wishlists list with two lines selected, Lampă de birou LED for Ana Popescu and Birou reglabil electric for Mihai Ionescu, and the Replenish button highlighted next to 2 selected](static/description/en/03_reaprovizionare_selectie.png)

4. In *Purchase > Orders > Requests for Quotation*, with the vendor *Group RFQ* left on
   *On Order* (the default), each replenished line created its own request for quotation to the
   product vendor, with *wishlist* as source document. With *Daily*, *Weekly* or *Always*, the
   need is added to an open request of the vendor instead.

   ![The Requests for Quotation list in Purchase: two new requests to Furnizor Mobilier SRL, in the RFQ status, with the order deadline Today and the totals 1,372.14 lei and 108.17 lei](static/description/en/04_cereri_oferta.png)

5. Open one of them: the line has a quantity of 1. Adjust the quantity if needed, then send or
   confirm it as usual. Clicking *Replenish* again creates new requests, it does not update the
   existing ones.

   ![A request for quotation in the RFQ status: vendor Furnizor Mobilier SRL highlighted and the line Lampă de birou LED with Quantity 1.00 highlighted and the 21% VAT tax, total 108.17 lei](static/description/en/05_cerere_oferta.png)
