  - Features:
    
      - Afisare valori atribute in functie de produsele determinate

in website\_sale.products\_attributes after: \<t t-foreach="attributes"
t-as="a"\> add \<t t-set="a\_value\_ids"
t-value="a.value\_ids.filtered(lambda v: v.id in value\_ids.ids)"/\>

replace t-foreach="a.value\_ids. with t-foreach="a\_value\_ids.
