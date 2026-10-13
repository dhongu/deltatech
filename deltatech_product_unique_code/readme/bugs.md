# Confirmed bugs — 2026-10-03

## UNIQUECODE-001 — P2: duplicates inside a write batch are excluded together

ProductProduct.write captures changed records then validates the complete changed recordset. _check_unique_field_all searches each value, but subtracts all products being validated (and all their templates) from matching records. Select two distinct products with different existing references and write the same new default_code on the recordset, where no other product already has that code. Both matching variants and both templates are removed from the duplicate candidates, so other_records is empty and the write passes, violating module uniqueness. Compare duplicate counts within the batch as well as against external records, or exclude only the current product/template per value check.

Evidence: full source, template inverse/single-variant code propagation, native barcode constraint and view contracts read. Source/set-membership proof for multi-record product.product.write; database write not executed. This finding is specifically default_code, which native product does not enforce with a uniqueness constraint. Native barcode validation can independently reject same-company barcode duplicates, so no blanket barcode-bypass claim.

## Limits

All eligible source reviewed. Sudo search deliberately covers archived/inaccessible products and error messages can reveal their display names; confidentiality policy not separately asserted. Global reference enforcement across companies and duplicate allowance group are explicit addon policy. Concurrent transactions without a database unique constraint require concurrency testing; not reported as a separately reproduced failure. Template multi-variant/dynamic creation paths need database validation. No database/permissions/concurrency tests executed.
