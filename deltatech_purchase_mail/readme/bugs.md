# Confirmed bugs — 2026-10-03

## PURMAIL-001 — P2: opening composer marks RFQs sent before sending

`action_compose_batch_email` posts a note to each selected order with mark_rfq_as_sent=True before returning the composer action. Native purchase.order.message_post (:479–483) immediately writes draft orders to sent. The request succeeds and commits before the user chooses Send; cancelling the composer leaves RFQs sent without an outgoing vendor email. The phase addon also moves them to rfq on this state write. Delay the transition until successful mail creation/sending according to the chosen delivery semantics, rather than composing.

Evidence: complete action and native message_post read; composer uses a transient aggregator without purchase-order message_post, so forwarding the context flag alone cannot perform the deferred purchase transition. No actual email sent or database composer cancellation executed.

## PURMAIL-002 — P2: exported description/code becomes an Excel formula

_build_xlsx writes product code and line.name through sheet.write, with no strings_to_formulas=False option. XlsxWriter defaults strings_to_formulas to True and dispatches strings starting with = to _write_formula. A literal product/line description such as =1+1 is stored as a formula instead of text in the supplier attachment. Externally entered descriptions can therefore inject workbook formulas; exact external-link/client effects are not asserted. Use write_string for text columns or disable formula interpretation for this export.

Evidence: addon source and installed XlsxWriter Worksheet._write_token_as_string implementation inspected; Worksheet().strings_to_formulas returned True. No generated attachment, Excel execution or malicious payload tested.

## Integration limits

Entire eligible source, auxiliary wizard ACL CSV, mail template/model, report XML ID/render signature, composer recipient/template logic and transient fallback in _action_send_mail_comment read. Generic mail.thread.message_notify supports non-thread aggregator models; absence of mail.thread inheritance is not itself an email-send crash. Selection enforces one vendor with email. XLSX omits currency/UoM columns despite allowing multiple orders: ambiguous summaries require business-format validation; no numerical conversion defect separately asserted. Native price_unit can include tax depending on vendor tax configuration, so its untaxed comment is not a verified contract. xlsxwriter import is unconditional; it is available locally, no dependency failure claimed. No database/mail/PDF/browser tests executed, and no external messages sent.
