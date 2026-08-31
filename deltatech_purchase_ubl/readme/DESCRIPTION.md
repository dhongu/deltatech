This module imports vendor invoices in UBL XML format and uses them to update purchase workflows in Odoo.

Key features:
- **Automatic vendor and order resolution**: the wizard keeps the selected purchase order on itself and can also identify the vendor and purchase order from the XML (`OrderReference`, supplier VAT, supplier name) when context is no longer available.
- **Automatic matching**: products are matched by barcode (GS1/EAN), supplier code, internal reference, or exact name.
- **Purchase order integration**:
    - existing matching lines are updated (quantity, price, discount) and lines whose product is not yet on the order are added, instead of being silently dropped;
    - the wizard warns before import when the order already has lines, so the user can review what will change;
    - when no purchase order is resolved, the wizard can still identify the vendor from XML and update supplier prices.
- **Price management**: updates vendor prices in `product.supplierinfo` directly from the XML data.
- **Discount support**: extracts line discounts from `AllowanceCharge` (`ChargeIndicator=false`) and applies them as percentage discounts on purchase order lines.
- **Total check**: compares the purchase order total with the XML total (`PayableAmount` / `TaxInclusiveAmount`, with untaxed fallback) and shows a warning when there is a difference.
- **Stock automation**: optionally validates the associated stock receipt by matching quantities from the XML.
- **Accounting**: optionally creates and links a vendor bill from the purchase order when an order is resolved.
- **Missing products**: option to automatically create missing products using data from the UBL file. Automated callers can pass `purchase_ubl_no_new_products` in context to leave unmatched lines unmatched instead of silently creating duplicates.
- **Mapping preview**: the interactive flow previews one row per invoice line with the product the matcher found and how it found it (green = supplier code or barcode, yellow = name only, red = no match); any row can be reassigned to a different product before confirming.
- **Unattended runs surface themselves**: a headless import whose total does not add up, or that leaves lines unmatched, posts a color-coded log and schedules a "SPV import needs review" to-do activity on the purchase order, assigned to its buyer.

The module supports standard UBL Invoice namespaces and common unit code mappings (C62, KGM, LTR, etc.).
