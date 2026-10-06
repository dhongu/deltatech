# Integrated source review — 2026-10-03

All eligible module source read, including inactive historical Python/XML. Active import graph includes product_template and res_company only. Manifest data loads only res_company_view.xml; oca_data_manual is not ordinary Odoo data loading. Old pricelist.py and pricelist/product view references are therefore not reported as live install/runtime failures.

Active currency compute traced through native product sale/cost currency fields, price computation and pricelist currency conversion. Native field dependency resolution gathers same-name method decorators across MRO, preserving company_id dependency even though the override has no decorator. Changes to company.price_currency_id are not explicitly declared dependencies; cached recomputation after editing that setting needs database verification before a separate finding is asserted.

Optional empty currency was investigated: native res.currency._convert supports an empty source by using the target, so an assumed singleton crash is excluded. Configuration semantics/monetary UI for empty main-company price currency remain validation limits. No new confirmed defect. No database/configuration/pricelist/browser tests executed.
