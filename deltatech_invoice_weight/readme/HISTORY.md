## 20.0.1.0.6 (2026-11-06)

- Port of 19.0.1.0.5: weights on invoices, sale and purchase orders convert the line
  quantity to the product unit (one dozen of a 2 kg product gives 24 kg, not 2 kg).
- The gross weight is converted to kg when product weights are configured in pounds.
- The two limitations are removed from the description.

## 20.0.1.0.5 (2026-11-03)

- Description rewritten from the code: removed the weight analysis in the
  Invoice Analysis pivot, which the module does not provide.
- Documented that the weights are calculated only when the document is created,
  and where each weight comes from; on 20.0 the line quantity is not converted
  to the product unit and pounds are not converted to kg (under Limitations).
- Banner: "Weight analysis in pivot view" replaced.

## 20.0.1.0.4 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.0.3 (2026-09-29)

- Own module icon, instead of the generic gears it had.
