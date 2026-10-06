# Bug review — deltatech_business_process_handover_document

Review date: 2026-10-02. Target version: Odoo 19.

## HANDOVER-001 — P2: Batch handover print includes annexes only for the last project

- **Status:** Open.
- **Location:** report/verbal_process_template.xml, report_bp_document.
- **Trigger:** Print Handover Document for two or more selected business projects.
- **Actual behavior:** The docs loop wraps only the introductory/signature section. Annex 1 and Custom Developments are rendered once after that loop and refer to o, which retains the final project value in the local Python QWeb compiler.
- **Evidence:** Entire template read. Parsed the exact XML and confirmed every o.handover_* annex loop has no docs-loop ancestor. Compared local ir.qweb._compile_directive_foreach, which assigns values[expr_as] for each item and leaves that final value in the mapping. No PDF rendering executed.
- **Impact:** The combined document contains introductions for all projects but omits test/development annexes for all except the last; reviewers can approve an incomplete handover.
- **Suggested fix:** Render each complete project document, including both annexes, inside its docs loop and use explicit page boundaries.
- **Validation needed:** Two projects with distinct processes/developments, reverse selection order, one empty project and a single-project report.

## Review limitations

All eligible source was manually read. Isolated method/XML reproductions and local framework/library source inspection do not establish database or browser integration coverage. No live credentials, external repository operations, Odoo database mutations or PDF rendering executed.
