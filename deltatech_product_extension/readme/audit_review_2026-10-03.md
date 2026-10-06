# Integrated source review — 2026-10-03

Complete eligible source read; product/partner fields and native view anchors checked. Native account.invoice.report._select has no SQL parameters in its current base implementation, includes template alias via _from, and does not aggregate with GROUP BY: appending template.manufacturer is valid against that contract. No new confirmed defect.

The override reconstructs SQL from super()._select().code and would lose parameters/flush metadata supplied by another extension; no concrete parameterized select producer established in this round, so retained as integration validation limit. Manufacturer domain is UI filtering, not an access restriction. Shelf-life unit policy and variant-specific dimensions not inferred. No database/report/view compilation tests executed.
