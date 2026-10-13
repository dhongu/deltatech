# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import models


class UomDomainMixin(models.AbstractModel):
    _name = "deltatech.uom.domain.mixin"
    _description = "Allow every unit convertible to the product's own unit"

    def _uom_domain_product_uom(self):
        """UM produsului fata de care se calculeaza unitatile convertibile."""
        self.ensure_one()
        return self.product_id.uom_id

    def _uom_domain_root(self):
        """Radacina arborelui de unitati din care face parte UM produsului.

        In 19.0 unitatile nu mai au categorie: fiecare are o unitate de referinta
        (`relative_uom_id`), iar `parent_path` e drumul pana la radacina arborelui.
        Doua unitati sunt convertibile intre ele exact cand au aceeasi radacina -
        vezi `uom.uom._has_common_reference()`. Radacina joaca deci rolul vechii
        categorii.
        """
        self.ensure_one()
        parent_path = self._uom_domain_product_uom().parent_path
        return parent_path.split("/")[0] if parent_path else False

    def _extend_allowed_uom_ids(self, field_name="allowed_uom_ids"):
        """Adauga in `field_name` toate unitatile convertibile la UM produsului.

        Odoo 19.0 a inlocuit filtrarea pe categorie cu o lista explicita per produs
        (`product.uom_ids`), asa ca o unitate existenta in baza nu mai apare nicaieri
        pana nu e legata de fiecare produs in parte. Metoda reface comportamentul de
        pana in 18.0: orice unitate din acelasi arbore devine selectabila.

        Se apeleaza din override-ul lui `_compute_allowed_uom_ids`, dupa `super()`,
        deci pastreaza ce calculeaza standardul (UM produsului, `uom_ids`, UM de pe
        furnizor). Nu declara `@api.depends` proprii: dependentele se acumuleaza peste
        MRO, iar cele native acopera deja `product_id.uom_id`.
        """
        uoms_by_root = {}
        for record in self:
            root = record._uom_domain_root()
            if root and root not in uoms_by_root:
                # un singur search per radacina, nu per linie
                uoms_by_root[root] = self.env["uom.uom"].search([("parent_path", "=like", f"{root}/%")])
        for record in self:
            root = record._uom_domain_root()
            if root:
                record[field_name] |= uoms_by_root[root]
