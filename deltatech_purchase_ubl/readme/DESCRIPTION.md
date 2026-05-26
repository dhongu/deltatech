This module allows importing vendor invoices in UBL XML format to automate purchase order management and accounting workflows.

Key features:
- **Automatic Matching**: Products are matched based on barcode (GS1/EAN), supplier code, internal reference, or name.
- **Purchase Order Integration**:
    - When launched from a purchase order, it can automatically add missing lines or update existing lines with quantities and prices from the XML.
    - Matches products specifically within the current order to ensure accuracy.
- **Price Management**: Updates supplier prices in the vendor pricelist (Supplier Info) directly from the XML data.
- **Discount Support**: Extracts line-level discounts (`AllowanceCharge` with `ChargeIndicator=false`) from UBL XML (e-Factura SPV format) and applies them as percentage discounts on purchase order lines.
- **Stock Automation**: Optionally validates the associated stock receipt (picking) by matching quantities from the XML.
- **Accounting**: Automatically creates and links a vendor bill from the purchase order after importing the XML data.
- **Missing Products**: Option to automatically create missing products using information from the UBL file.

The module supports standard UBL Invoice namespaces and common unit code mappings (C62, KGM, LTR, etc.).
