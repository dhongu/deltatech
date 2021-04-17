Features:
 - Afisare valori atribute in functie de produsele determinate

in website_sale.products_attributes
after:
<t t-foreach="attributes" t-as="a">
add
<t t-set="a_value_ids" t-value="a.value_ids.filtered(lambda v: v.id in value_ids.ids)"/>

replace t-foreach="a.value_ids. with t-foreach="a_value_ids.
