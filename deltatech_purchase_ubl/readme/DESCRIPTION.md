am This module imports vendor invoices in UBL XML format and uses them to update purchase workflows in Odoo.

Key features:
- **Automatic vendor and order resolution**: the wizard keeps the selected purchase order on itself and can also identify the vendor and purchase order from the XML (`OrderReference`, supplier VAT, supplier name) when context is no longer available.
- **Automatic matching**: products are matched by barcode (GS1/EAN), supplier code, internal reference, or exact name.
- **Purchase order integration**:
    - when the purchase order already has lines, the import updates only the existing matching lines;
    - new XML lines are not added to an existing order, and the wizard shows this warning before import;
    - when no purchase order is resolved, the wizard can still identify the vendor from XML and update supplier prices.
- **Price management**: updates vendor prices in `product.supplierinfo` directly from the XML data.
- **Discount support**: extracts line discounts from `AllowanceCharge` (`ChargeIndicator=false`) and applies them as percentage discounts on purchase order lines.
- **Total check**: compares the purchase order total with the XML total (`PayableAmount` / `TaxInclusiveAmount`, with untaxed fallback) and shows a warning when there is a difference.
- **Stock automation**: optionally validates the associated stock receipt by matching quantities from the XML.
- **Accounting**: optionally creates and links a vendor bill from the purchase order when an order is resolved.
- **Missing products**: option to automatically create missing products using data from the UBL file.

The module supports standard UBL Invoice namespaces and common unit code mappings (C62, KGM, LTR, etc.).
