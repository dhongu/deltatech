The module has no menus of its own: the badge appears on the fields where other modules use it.
The steps below use the sale order phase from `deltatech_sale_stage`; the purchase order phase
(`deltatech_purchase_phase`) behaves the same way.

1. Go to **Sales → Orders → Orders**. The **Phase** column shows the phase of each order as a
   colored badge, one color per phase.

   ![Sales Orders list with six confirmed orders; the Phase column shows the colored badges Confirmed, Order sent, Delivered and Shipped; the Delivered badge on the third row is highlighted](static/description/en/01_lista_comenzi_faze.png)

2. Open an order. The **Phase** field shows the badge; hovering it shows **×**, which removes the
   value and brings back the search box to pick another phase.

   ![Sales order S00002 for Ionescu Andrei: the Phase field with the blue Confirmed badge and the × to remove it](static/description/en/02_comanda_eticheta_faza.png)

3. Click the badge to open the color picker (11 colors). The chosen color is saved on the phase
   right away, not on the order, so every order with that phase shows the new color. Saving it
   requires write access on the phases (Sales / Administrator).

   ![Sales order S00002 with the color picker open under the Confirmed badge: 11 colored circles to choose the phase color from](static/description/en/03_alegere_culoare.png)

The colors of all the badges on screen are read with a single request to the server.
