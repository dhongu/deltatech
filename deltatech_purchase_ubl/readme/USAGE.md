1. Open a **Purchase Order** and click the **Import UBL** button in the header.
2. Select the vendor invoice file in **UBL XML** format (e-Factura format is
   supported). If the wizard is opened from an order, that order is used;
   otherwise the vendor and, if possible, the order are identified from the
   XML (order reference, supplier VAT/name).
3. Choose the import options:
   - **Automatically create storable products** for XML lines that cannot be
     matched to an existing product (matched by barcode, supplier code,
     internal reference or name).
   - **Update vendor prices** — write the XML unit prices into the product's
     vendor pricelist (`product.supplierinfo`).
   - **Create a vendor bill** from the XML invoice data.
   - **Validate the receipt** — set the done quantities on the linked stock
     receipt from the XML and validate it.
4. Click **Import**. If the order already has lines, only matching existing
   lines are updated (new XML lines found on the invoice are never added
   automatically — a warning is shown before import). Line discounts found on
   the XML are applied as a percentage discount on the matching order lines.
5. If the purchase order total differs from the XML total, a warning is shown
   before import so it can be reviewed.
6. After import, review the result log; if a vendor bill was created, use the
   **View Vendor Bill** button to open it directly.
