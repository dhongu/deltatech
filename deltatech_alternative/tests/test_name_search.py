# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAlternativeNameSearch(TransactionCase):
    """Searching by alternative code keeps the caller's domain (ALTERNATIVE-001)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param("alternative.search_name", "True")
        cls.categ_other = cls.env["product.category"].create({"name": "Other category"})
        cls.tmpl_sale = cls.env["product.template"].create(
            {"name": "Sellable part", "default_code": "SALE1", "sale_ok": True}
        )
        cls.tmpl_nosale = cls.env["product.template"].create(
            {
                "name": "Internal part",
                "default_code": "NOSALE1",
                "sale_ok": False,
                "categ_id": cls.categ_other.id,
            }
        )
        cls.env["product.alternative"].create(
            [
                {"name": "OEMALT-777", "product_tmpl_id": cls.tmpl_sale.id},
                {"name": "OEMALT-777", "product_tmpl_id": cls.tmpl_nosale.id},
            ]
        )
        cls.variant_sale = cls.tmpl_sale.product_variant_id
        cls.variant_nosale = cls.tmpl_nosale.product_variant_id

    def _ids(self, res):
        return {r[0] for r in res}

    def test_template_without_domain(self):
        res = self.env["product.template"].name_search("OEMALT-777")
        self.assertEqual(self._ids(res), {self.tmpl_sale.id, self.tmpl_nosale.id})

    def test_template_keeps_domain(self):
        Template = self.env["product.template"]
        res = Template.name_search("OEMALT-777", domain=[("sale_ok", "=", True)])
        self.assertEqual(self._ids(res), {self.tmpl_sale.id})
        res = Template.name_search("OEMALT-777", domain=[("categ_id", "=", self.categ_other.id)])
        self.assertEqual(self._ids(res), {self.tmpl_nosale.id})

    def test_template_limit(self):
        res = self.env["product.template"].name_search("OEMALT-777", limit=1)
        self.assertEqual(len(res), 1)
        res = self.env["product.template"].name_search("OEMALT-777", limit=None)
        self.assertEqual(self._ids(res), {self.tmpl_sale.id, self.tmpl_nosale.id})

    def test_variant_keeps_domain(self):
        Product = self.env["product.product"]
        res = Product.name_search("OEMALT-777")
        self.assertEqual(self._ids(res), {self.variant_sale.id, self.variant_nosale.id})
        res = Product.name_search("OEMALT-777", domain=[("sale_ok", "=", True)])
        self.assertEqual(self._ids(res), {self.variant_sale.id})

    def test_variant_display_name_and_limit(self):
        res = self.env["product.product"].name_search("OEMALT-777", domain=[("sale_ok", "=", True)], limit=None)
        self.assertEqual(res, [(self.variant_sale.id, self.variant_sale.display_name)])
        self.assertEqual(self.variant_sale.display_name, "[SALE1] Sellable part")

    def test_other_company_product_excluded(self):
        company = self.env.company
        company2 = self.env["res.company"].create({"name": "Alternative Co 2"})
        tmpl_c2 = self.env["product.template"].create({"name": "Company 2 part", "company_id": company2.id})
        self.env["product.alternative"].create({"name": "OEMALT-777", "product_tmpl_id": tmpl_c2.id})
        user = self.env["res.users"].create(
            {
                "name": "Alternative user",
                "login": "alternative_user",
                "company_id": company.id,
                "company_ids": [(6, 0, company.ids)],
                "group_ids": [(6, 0, self.env.ref("base.group_user").ids)],
            }
        )
        env = self.env(user=user, context=dict(self.env.context, allowed_company_ids=company.ids))
        res = env["product.template"].name_search("OEMALT-777")
        self.assertEqual(self._ids(res), {self.tmpl_sale.id, self.tmpl_nosale.id})
        res = env["product.product"].name_search("OEMALT-777")
        self.assertEqual(self._ids(res), {self.variant_sale.id, self.variant_nosale.id})
