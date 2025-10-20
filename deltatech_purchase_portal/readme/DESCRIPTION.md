Purchase Portal enhancements for vendor collaboration

Overview
This module extends the standard Purchase portal so your vendors can collaborate directly on Requests for Quotation (RFQs) from the portal. Vendors can edit the unit price and the line description (multiline), and they can accept and sign an RFQ using the same signature flow used for Sales Orders. All actions are protected by secure access tokens and business-state rules.

Key features
- Edit per line on RFQs (state: sent):
  - Unit Price: inline number field.
  - Description (name): multiline textarea, supports line breaks.
- Clean portal UI:
  - “Edit” button visible only on RFQs; switches the page to edit mode.
  - In edit mode, a “Display” button allows returning to the read-only view.
  - Proper icon spacing consistent with the standard “View Details” button.
  - Description field displayed inline with the product image for a tidy layout.
- Accept & Sign (like Sales Orders):
  - Signature modal (portal.signature_form) to capture handwritten signature and signer name.
  - Confirms the RFQ into a Purchase Order upon successful signature.
  - Stores signed_by, signed_on, and signature on the purchase order.
  - Attaches the signed PDF to the chatter for traceability.
- Secure by design:
  - Access controlled via the standard portal access token.
  - Inline edits are allowed only when the order is in state “sent”.
  - Display-type lines cannot be edited.

How it works
- From the RFQ portal page, click Edit to switch to edit mode. You can then modify the unit price and the line description. Edits are sent to the server with small, debounced requests and saved immediately.
- Back in normal mode, use the “Accept & Sign” button to open the signature modal, sign, and confirm the RFQ.

Technical notes
- Adds fields on purchase.order: signed_by (Char), signed_on (Datetime), signature (Binary).
- Adds vendor_note on purchase.order.line (kept for compatibility), although the portal now edits the core line description (name).
- Provides a JSON route to update price/description for lines, with access/state validation.
- Reuses Odoo’s purchase portal controller for access checks and base rendering.
- Frontend logic is delivered via a small JS module loaded in web.assets_frontend.



Installation & upgrade
1) Install the module from Apps or add it to your addons path and update the app list.
2) Upgrade the module after changes to ensure templates and assets are rebuilt (e.g., -u deltatech_purchase_portal).

Usage
- Share the RFQ portal link with your vendor (it includes a secure access_token).
- Vendor can:
  - Click Edit to adjust Unit Price and Description per line.
  - Click Display to exit edit mode.
  - Click Accept & Sign to sign and confirm the RFQ.

Limitations
- Editing is restricted to RFQs in state “sent”; confirmed orders are read-only in the portal.
- Display-type lines (sections/notes) cannot be edited.

Support
For help or customizations, please contact Terrabit (https://www.terrabit.ro).
