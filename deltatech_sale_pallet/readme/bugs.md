# Identified bugs

Reviewed: 2026-10-01

Target version: Odoo 20.0

Scope: Source review and real ORM reproductions in the separate audit database.

## [P2] Approximate floor and ceiling produce incorrect pallet counts

**Status:** Open — documented, not fixed.

**Location:** `models/sale.py:67–71`. Line numbers refer to the reviewed source.

### Cause

The code approximates floor and ceiling with round(ratio - 0.49) and round(ratio + 0.49). These formulas cross thresholds incorrectly for fractional quantities. The description promises increases at the next full multiple of the minimum.

### Impact

The normal onchange can charge an extra pallet before the next threshold. The alternate mode can undercount a partially filled pallet.

### Reproduction

Set pallet_qty_min=10. Quantity 19.95 in delete_if_under mode returns 2 rather than 1; quantity 10.05 in the alternate mode returns 1 rather than 2.

### Recommended correction

Use explicit floor/ceiling with a deliberate precision policy suitable for the product UoM.

### Validation

Confirmed using actual sale.order.line records: the results were 2 and 1 respectively. The transaction was rolled back.

## [P1] Sale quantities are compared to pallet thresholds without UoM conversion

**Status:** Open — documented, not fixed.

**Location:** `models/sale.py:60–67`. Line numbers refer to the reviewed source.

### Cause

pallet_qty_min is a product-template quantity, also used with the product list price in models/product_template.py:23. The pallet helper compares it to the numeric sale-line quantity without converting product_uom_id to product.uom_id.

### Impact

Selling the same physical quantity in a different unit can omit or multiply charged pallets.

### Reproduction

A product uses Units with a minimum of 10 units per pallet. Sell 2 dozens, equivalent to 24 units. The onchange mode returns 0 pallets instead of 2.

### Recommended correction

Convert the sale quantity into the product reference UoM before checking the threshold and calculating pallet counts.

### Validation

Confirmed with real ORM records and a dozen UoM whose relative factor is 12: actual count 0 for 24 reference units. The transaction was rolled back.

## [P2] Removing the final goods line leaves its automatic pallet line

**Status:** Open — documented, not fixed.

**Location:** `models/sale.py:12–23`. Line numbers refer to the reviewed source.

### Cause

The onchange only updates pallet products present in the recomputed map. Once the last goods line requiring a pallet is removed or changed to a non-pallet product, its old pallet is absent from the map and is never removed or reset.

### Impact

A quotation retains a pallet charge and a pallet quantity despite containing no goods that require it.

### Reproduction

Create an onchange order with 10 units of a product requiring one pallet. Run the onchange and confirm one pallet line exists. Remove the goods line and run the onchange again; the pallet line remains at quantity 1.

### Recommended correction

Track which lines were automatically generated and remove or reset obsolete ones. Preserve deliberately added manual pallet lines according to an explicit policy.

### Validation

Confirmed on real Odoo new-record onchange objects. The initial pallet was automatically linked by the ORM inverse; after removing the goods, zero goods lines and one pallet remained. The transaction was rolled back.

## [P2] Pallet price cache is not invalidated when its inputs change

**Status:** Open — documented, not fixed.

**Location:** `models/product_template.py:14–24`. Line numbers refer to the reviewed source.

### Cause

The nonstored computed pallet_price uses pallet_product_id.list_price, pallet_qty_min and list_price, but its method only has api.onchange, with no api.depends declaration. Changing a price does not invalidate an already computed pallet_price in the same environment.

### Impact

Repeated reads or form onchanges in the same environment can display or use a stale pallet price. A fresh environment may recompute correctly; this finding does not claim the stale value is stored in the database.

### Reproduction

Pallet price 20 plus 10 goods at list price 5 gives 70. Read pallet_price, write goods list_price=8, and read again in the same environment. The result remains 70 instead of 100.

### Recommended correction

Declare all compute dependencies, including related pallet product price and the product list price, and retain an onchange only where independently needed.

### Validation

Confirmed using actual product.template records: before=70, after=70, expected=100. The transaction was rolled back.

## Existing test suite

The module test suite ran on 2026-10-01 in test20_bug_audit_20261001: one test completed with zero failures and zero errors. It exercises a sale of 100 units but does not assert the four edge cases above. Separate ORM reproductions confirmed all four; their transaction was rolled back.
