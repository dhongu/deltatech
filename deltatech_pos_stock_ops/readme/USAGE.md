## Set up

1. Go to **Point of Sale ‣ Configuration ‣ Settings**, choose the register and, in the **Stock Operations** block, tick **Receipts from the POS** and/or **Deliveries from the POS**.
2. Check **Receipt Operation Type** and **Delivery Operation Type**; they are proposed from the register's warehouse.
3. Give each cashier who may use it the **POS stock operations** right (**Settings ‣ Users**).

![Stock Operations settings block with the two options and the operation types](static/description/en/01_setari_pos.png)

## Deliver from the register

1. Open the register menu: **Receipt** and **Delivery** appear after *Reload Data*.

![Register menu with the Receipt and Delivery entries](static/description/en/02_meniu_pos.png)

2. Choose **Delivery**, scan a product (or a pack barcode) or type part of its name and pick it from the list.
3. Adjust the quantity, optionally choose a **Partner**, and press **Validate**.

![Delivery dialog with one product line](static/description/en/03_livrare.png)

The delivery transfer is created and validated, and the stock drops.

![Notification confirming the delivery transfer was validated](static/description/en/04_livrare_validata.png)

## Receive against a purchase order

There is no free receipt: goods are received only against a confirmed purchase order of the register's warehouse.

1. Choose **Receipt** in the register menu. The dialog lists the purchase orders still to receive; search by order number, supplier or transfer.

![Receipt dialog listing the purchase orders to receive](static/description/en/05_receptie_comenzi.png)

2. Pick the order, then type the quantity that actually arrived on each line (0 leaves a line out). Scanning a product barcode sets its quantity to 1 and then counts up.
3. Press **Validate**. What did not arrive stays on the same purchase order as a backorder.

![Receipt dialog with the received quantity typed on each line](static/description/en/06_receptie_linii.png)

## Review the operations

**Point of Sale ‣ Orders ‣ Stock Operations** lists every operation with its transfer, partner, purchase order (receipts), register, user and state. **Needs confirmation** means Odoo asked for a manual step: finish that transfer in Inventory.

![List of POS stock operations with their transfers and states](static/description/en/07_jurnal.png)
