**Configure the postponed delivery**

1. On a payment provider (**Accounting → Configuration → Online Payments**), tick **Postponed
   Delivery**. When an order paid through this provider is confirmed before the payment is done, its
   deliveries are postponed; they are released automatically when the payment is confirmed.

   ![Payment provider form with the Postponed Delivery option ticked](static/description/en/01_furnizor_plata_livrare_amanata.png)

2. On a sales team (**Sales → Configuration → Teams**), tick **Postpone delivery for transfer
   payment** to postpone the deliveries of the team's orders paid by wire transfer. These deliveries are
   released manually, once the payment is received.

   ![Sales team form with the Postpone delivery for transfer payment option ticked](static/description/en/02_echipa_vanzari_transfer.png)

3. Optionally, **Postponed** on an operation type makes the transfers created manually from that
   operation type start postponed. The system parameter `backorders.postponed` = `True` does the same
   for the backorders.

   ![Delivery Orders operation type with the Postponed option](static/description/en/03_tip_operatie_amanat.png)

**Postpone and release a delivery**

1. On a confirmed sale order, click **Postpone**: all the deliveries of the order that are not done or
   cancelled become postponed.

   ![Confirmed sale order S00201 with the Postpone button](static/description/en/04_comanda_buton_amana.png)

2. A postponed delivery shows the **Postponed** ribbon and waits, even if the products are reserved.

   ![Postponed delivery of order S00202, with the Postponed ribbon and the Postponed field ticked](static/description/en/05_livrare_amanata.png)

3. A postponed delivery cannot be validated: **Validate** stops with an error.

   ![Error dialog: the transfer is postponed](static/description/en/06_validare_refuzata.png)

4. The **Postponed delivery** filter of the sale orders lists the orders waiting for release; on the
   transfers, the same role has the **Postponed** filter.

   ![Sales Orders list with the Postponed delivery filter: order S00202](static/description/en/07_comenzi_filtru_amanate.png)

5. Once the payment is received, click **Release** on the order. The **Postpone Delivery** and
   **Release Delivery** actions do the same on several orders at once.

   ![Sale order S00202 with the Release button](static/description/en/08_comanda_buton_elibereaza.png)

**Follow the availability and the parcel**

1. On the transfers in progress, **Available state** shows whether the products are reserved:
   available, partially available or unavailable.

   ![Deliveries list with the availability column](static/description/en/09_livrari_disponibilitate.png)

2. On a done delivery, **Delivery State** shows where the parcel is at the carrier, from *Ready in
   warehouse* to *Delivered* or *Refused*. The shipping integrations update it; it can also be set by
   hand.

   ![Done delivery DC/OUT/00003 with the Delivery State In Transit](static/description/en/10_livrare_stare_colet.png)
