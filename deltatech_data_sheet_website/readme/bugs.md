# Bug review — Data Sheet Website

Review date: 2026-10-02. Target version: Odoo 19.

## DATASHEETWEB-001 — P2: Data sheet links disappear when no standard product documents exist

- **Status:** Open.
- **Location:** views/templates.xml, product_data_sheet; native website_sale.product product_documents block.
- **Trigger:** Assign a public data_sheet_id or safety_data_sheet_id attachment to a product with no standard product.document marked shown_on_product_page.
- **Actual behavior:** The inherited template inserts both links inside div#product_documents. The native ancestor has t-if=product_documents, where the variable contains only the standard shown product documents. Custom attachment fields do not populate that collection; the entire ancestor and its inserted links are skipped.
- **Evidence:** Compared actual XPath position=inside with native website_sale/views/templates.xml: product_documents is assigned from product_document_ids.filtered(shown_on_product_page), and the div is conditional on that collection. An empty collection suppresses the subtree independently of the custom attachment fields. No browser render executed.
- **Impact:** Valid configured technical/safety PDFs remain unavailable from the product page unless an unrelated standard product document also exists.
- **Suggested fix:** Extend the container condition to include either custom attachment, or render the links in an independent section outside the document-only conditional.
- **Validation needed:** Only technical sheet, only safety sheet, both sheets, no sheets and standard product documents present/absent; anonymous downloads.

## Review limitations

All eligible Python/XML source was read and native QWeb condition compared. No website/browser, attachment-download or Odoo integration tests executed.
