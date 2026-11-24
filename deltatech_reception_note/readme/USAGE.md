The module separates what was **ordered** from what was **delivered**: the open quantities of a
purchase order are copied to an *RFQ Only* request, and each delivery is entered on a *Reception Note*
purchase order that draws on those requests when it is confirmed. No configuration is needed after
installation; the **Purchase → Reception notes** menu appears.

1. **Start from the confirmed order** — open a purchase order of **Type** *Normal* (1), click the gear
   next to its name and choose **Create reception note**.

   ![Confirmed Normal purchase order with the gear menu open on Create reception note](static/description/en/01_comanda_actiune_creeaza_rfq.png)

2. **Confirm** — in the **Create reception note** dialog, click **Apply** (1). The action works only
   on *Normal* orders. The order's receipts that are *Ready* are cancelled, so the goods are received
   only through reception notes.

   ![Create reception note dialog with the Apply button](static/description/en/02_asistent_creeaza_rfq.png)

3. **Check the RFQ Only request** — a new request of **Type** *RFQ Only* (1) is created in the *RFQ
   Sent* state, with the same vendor, vendor reference, currency, fiscal position, payment terms,
   prices and taxes, and the quantity not received yet in the **Quantity** column. It has no **Confirm Order**
   button: it only keeps the quantities expected from the vendor. An *RFQ Only* request entered by
   hand is marked as sent with **Set as sent**; only sent requests are consumed.

   ![RFQ Only request in the RFQ Sent state with the open quantities](static/description/en/03_cerere_doar_rfq.png)

4. **Enter the delivery** — when the goods arrive, go to **Purchase → Reception notes → Prepare
   reception note** and click **New**. The **Type** is *Reception Note* (1). Choose the vendor, fill in
   the vendor's **Delivery Note No** (2), add the products and the quantities actually delivered,
   leave **Ignore quantities** (3) unticked and click **Confirm Order** (4). The **Send RFQ** button
   has no effect on a reception note.

   ![Draft reception note with Type, Delivery Note No, Ignore quantities and Confirm Order](static/description/en/04_nota_receptie_ciorna.png)

5. **Quantity not found** — the quantities are looked up on the sent *RFQ Only* requests of the same
   vendor and company. If a product is missing or the note holds more than what is left, the
   confirmation stops and names the product and the missing quantity. Correct the note, or tick
   **Ignore quantities** if the vendor really delivered more.

   ![Invalid Operation dialog: the quantity of the cement product is not found in a sent RFQ](static/description/en/05_eroare_cantitate_negasita.png)

6. **Confirmed note** — the note becomes a *Purchase Order* and the standard receipt is created,
   available from the **Receipt** smart button (1). Validate it as usual. A confirmed note leaves the
   **Prepare reception note** list; find it under **Purchase → Orders → Purchase Orders**.

   ![Confirmed reception note with the Receipt smart button](static/description/en/06_nota_confirmata.png)

7. **Forced quantities** — with **Ignore quantities** (1) ticked, the note is confirmed anyway: what is
   found is taken from the requests, and the products or quantities not found are listed in the
   chatter, so they can be checked later. The message is written in the language of the user who
   confirmed the note (Romanian in the screenshot).

   ![Reception note confirmed with Ignore quantities and the forced quantities message in the chatter](static/description/en/07_nota_cantitati_fortate.png)

8. **Remaining quantities** — notes draw from the vendor's oldest sent request first. In the example,
   that is an earlier *RFQ Only* request of 100 bags of cement and 50 of adhesive: its **Quantity**
   column now shows what the vendor still has to deliver, 40 and 30 after the note of 60 and 20. Quantities are
   compared in the product's unit of measure, so a note in packs draws correctly from a request in
   units. A request with every line at zero is marked as empty; use the **Not empty** and **Empty**
   search filters to find them.

   ![RFQ Only request after consumption, with the remaining quantities](static/description/en/08_cerere_dupa_consum.png)

9. **Receipts to validate** — **Purchase → Reception notes → To arrive** lists the incoming transfers
   in the *Ready* state; find each note by the **Source Document** column. Validated receipts appear
   in **To invoice**, whether they were billed or not.

   ![To arrive list with the Ready receipts of the vendor](static/description/en/09_receptii_pe_drum.png)
