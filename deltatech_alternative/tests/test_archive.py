# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestProductArchive(TransactionCase):
    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].sudo().set_param("alternative.search_name", "True")

    def test_search_archived_product_by_alternative_code(self):
        # Creare produs activ cu cod alternativ
        product_active = self.env["product.template"].create(
            {
                "name": "Active Product",
                "alternative_code": "ALT_ACTIVE",
                "active": True,
            }
        )

        # Creare produs arhivat cu cod alternativ
        product_archived = self.env["product.template"].create(
            {
                "name": "Archived Product",
                "alternative_code": "ALT_ARCHIVED",
                "active": False,
            }
        )

        # Căutare după codul alternativ al produsului activ
        res_active = self.env["product.template"].name_search("ALT_ACTIVE", operator="ilike")
        ids_active = [r[0] for r in res_active]
        self.assertIn(product_active.id, ids_active, "Produsul activ ar trebui să fie găsit după codul alternativ")

        # Căutare după codul alternativ al produsului arhivat
        res_archived = self.env["product.template"].name_search("ALT_ARCHIVED", operator="ilike")
        ids_archived = [r[0] for r in res_archived]
        self.assertNotIn(
            product_archived.id, ids_archived, "Produsul arhivat NU ar trebui să fie găsit după codul alternativ"
        )

    def test_search_archived_variant_by_alternative_code(self):
        # Creare produs activ cu cod alternativ
        product_active = self.env["product.product"].create(
            {
                "name": "Active Variant",
                "alternative_code": "VALT_ACTIVE",
                "active": True,
            }
        )

        # Creare produs arhivat cu cod alternativ
        product_archived = self.env["product.product"].create(
            {
                "name": "Archived Variant",
                "alternative_code": "VALT_ARCHIVED",
                "active": False,
            }
        )

        # Căutare după codul alternativ al produsului activ
        res_active = self.env["product.product"].name_search("VALT_ACTIVE", operator="ilike")
        ids_active = [r[0] for r in res_active]
        self.assertIn(product_active.id, ids_active, "Varianta activă ar trebui să fie găsită după codul alternativ")

        # Căutare după codul alternativ al produsului arhivat
        res_archived = self.env["product.product"].name_search("VALT_ARCHIVED", operator="ilike")
        ids_archived = [r[0] for r in res_archived]
        self.assertNotIn(
            product_archived.id, ids_archived, "Varianta arhivată NU ar trebui să fie găsită după codul alternativ"
        )
