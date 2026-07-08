- **Product cost category**: on a **Product Category** (Inventory /
  Manufacturing > Configuration > Product Categories), set the new
  **Cost Category** field to *Raw materials*, *Semi-products* or
  *Packing Material*. This classification is used to break down
  manufacturing costs by type of consumed material.
- **Costs tab on a Manufacturing Order**: open a manufacturing order
  (Manufacturing > Operations > Manufacturing Orders) and use the new
  **Costs** notebook tab to see the value of raw materials, semi-finished
  products and packing material consumed by the order. Click **Update**
  on that tab to recompute the breakdown after new components have been
  consumed.
- **Production Cost Analysis report**: go to **Manufacturing > Reporting
  > Production Cost Analysis** for a pivot/list/graph report of
  planned vs. actual produced quantities and values, consumed material
  cost split by category (raw/packing/semi-finished), and standard vs.
  actual cost per manufacturing order — filterable and groupable by
  product, lot, date, and state.
- Remember to add roughly a 20% coefficient on top of the raw material
  cost when evaluating true production cost, to account for indirect
  costs not captured by the report.

Note: the manifest also documents planned BOM/production changes
(`value_overhead` field on Bills of Materials, automatic
`date_expected` adjustments, automatic production lot generation, and
an `onchange_product_id` helper); in the current codebase these are
present only as commented-out view code and are not active.
