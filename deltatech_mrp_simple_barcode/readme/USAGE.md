This is an extension of `deltatech_mrp_simple` that adds barcode support to the Simple Production screen (requires the `barcodes` module).

1. Open a **Simple Production** record (**Inventory > Simple Production**) while it is still in draft.
2. Scan a product's barcode with a barcode reader (or the on-screen scanner).
3. If the product is already in the **Consumed** lines, its quantity is increased by 1; otherwise a new consumed line is added for it.
4. If no product matches the scanned barcode, the module retries the lookup using the product's internal reference.
5. Scanning is only allowed while the record is in draft — once it is confirmed, scanning shows an error instead of modifying the lines.
