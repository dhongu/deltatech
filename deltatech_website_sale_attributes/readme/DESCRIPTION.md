Hides chosen attribute values from the online shop while keeping them on the products in the back
office.

**Visibility per attribute value.** Each value of a product attribute gets a *Visibility* field,
*Visible* (default) or *Hidden*, shown in the values list of the attribute form. Odoo has the same
choice for a whole attribute; this one works on single values.

**Hidden on the product page.** When the shop shows a product, the hidden values are left out of the
active values of its attribute lines, so the customer cannot choose them in the variant selector. In
the back office the values remain available on the products, sales orders and variants.

**Where to configure it.** *Website > eCommerce > Products > Attributes* (or *Sales > Configuration >
Products > Attributes*), open the attribute and set *Visibility* on the values to hide. The menu is
available when *Variants* is enabled in the settings.

## Limitations

- The attribute filters in the shop sidebar still list the hidden values.
- The shop page override computes a list of visible values (`value_ids`) that no standard template
  reads, so it has no effect on the shop page by itself.
