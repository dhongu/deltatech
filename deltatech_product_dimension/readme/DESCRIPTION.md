Transport, storage and delivery quotes need to know how much room a product takes. This module adds length, width and height to the product form and calculates the volume from them.

- **Dimension row**: The product form shows a *Dimension* row above *Volume*: three fields for length, width and height, written as L x W x H and followed by "cm". Each starts at 1 on a new product.
- **Automatic volume**: Changing any of the three values recalculates *Volume* as length × width × height ÷ 1,000,000, which gives cubic meters from centimeters.
- **Volume unit**: The module does not convert the result to the volume unit configured for the database, so it stays in cubic meters.
- **Zero dimension**: If one of the three values is zero, the volume is not recalculated and keeps its previous value.
- **Product level**: The fields belong to the product template, so all variants of a product share the same dimensions.

The module depends only on Product (`product`) and defines no access rules or menus of its own. The volume is recalculated only when a dimension is edited in the form, so imports and API writes do not update it.
