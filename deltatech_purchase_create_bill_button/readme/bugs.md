# Confirmed bugs — 2026-10-03

## PURBILLBUTTON-001 — P2: batch bill loses other vendor references

_prepare_invoice copies each PO.partner_ref into ref/payment_reference. Native purchase.order.action_create_invoice groups prepared dictionaries by company/vendor/currency, concatenates invoice lines and origins, but keeps other scalar fields from the first dictionary (:791–809). Selecting two compatible RFQs/POs with references A and B in the new Create Bills list action generates one bill with both orders' lines but only A in ref/payment_reference. B is silently lost despite the extension's reference-copy feature. Reconcile all relevant references explicitly when grouping, with a deliberate payment-reference policy, or prevent grouping when references must stay distinct.

Evidence: complete addon model/views/assets and native preparation/grouping source read. Source-only, no batch database billing test executed. Requires adjacent compatible dictionaries in native groupby; does not claim native grouping merges every non-adjacent compatible order.

## Limits

Native action_create_invoice, purchase form uploader/header anchors and purchase.ListView/web.ListView template anchors exist. Local native method does not have the common upstream invoice_status guard: do not assume its list invocation rejects uninvoicable selections. Button visibility only constrains the form, while native billing scope and draft quantities require workflow validation; no additional bill-state defect asserted in this pass. No database/browser/OWL compilation tests executed.
