# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from base64 import b64encode

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .test_ubl_import import _xml_invoice


@tagged("post_install", "-at_install")
class TestUblImportIssues(TransactionCase):
    """Duplicate check per company, vendor price per variant/company, SET unit."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.company_b = cls.env["res.company"].create({"name": "UBL Second Company"})
        cls.env.user.company_ids |= cls.company_b
        cls.Wizard = cls.env["purchase.ubl.import.wizard"]
        cls.vendor = cls.env["res.partner"].create(
            {"name": "Issues Vendor SRL", "is_company": True, "vat": "RO30000003", "supplier_rank": 1}
        )
        cls.unit = cls.env.ref("uom.product_uom_unit")

    # ------------------------------------------------------------------
    # Duplicate vendor bill (#3438)
    # ------------------------------------------------------------------
    def test_duplicate_bill_is_searched_in_the_company(self):
        bill = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.vendor.id,
                "ref": "DUP-REF-1",
                "company_id": self.company.id,
            }
        )
        wiz = self.Wizard.with_company(self.company_b).with_context(
            allowed_company_ids=[self.company_b.id, self.company.id]
        )
        self.assertFalse(wiz._find_duplicate_bill(self.vendor, "DUP-REF-1"))
        self.assertFalse(wiz._find_duplicate_bill(self.vendor, "DUP-REF-1", company=self.company_b))
        self.assertEqual(wiz._find_duplicate_bill(self.vendor, "DUP-REF-1", company=self.company), bill)
        bill.button_cancel()
        self.assertFalse(wiz._find_duplicate_bill(self.vendor, "DUP-REF-1", company=self.company))

    # ------------------------------------------------------------------
    # Vendor price per variant and company (#3439)
    # ------------------------------------------------------------------
    def _variants(self):
        attribute = self.env["product.attribute"].create(
            {"name": "UBL Size", "value_ids": [(0, 0, {"name": "S"}), (0, 0, {"name": "L"})]}
        )
        template = self.env["product.template"].create(
            {
                "name": "UBL Shirt",
                "attribute_line_ids": [
                    (0, 0, {"attribute_id": attribute.id, "value_ids": [(6, 0, attribute.value_ids.ids)]})
                ],
            }
        )
        return template, template.product_variant_ids[0], template.product_variant_ids[1]

    def test_supplier_price_keeps_other_variant_row(self):
        template, variant_a, variant_b = self._variants()
        row_a = self.env["product.supplierinfo"].create(
            {
                "partner_id": self.vendor.id,
                "product_tmpl_id": template.id,
                "product_id": variant_a.id,
                "product_code": "CODE-A",
                "price": 10.0,
            }
        )
        self.Wizard._update_supplier_price(self.vendor, variant_b, "CODE-B", 80.0, "RON")
        self.assertRecordValues(row_a, [{"product_id": variant_a.id, "product_code": "CODE-A", "price": 10.0}])
        row_b = template.seller_ids.filtered(lambda s: s.product_id == variant_b)
        self.assertRecordValues(row_b, [{"product_code": "CODE-B", "price": 80.0}])
        # a second import of B updates its own row, without a duplicate
        self.Wizard._update_supplier_price(self.vendor, variant_b, "CODE-B", 85.0, "RON")
        self.assertEqual(len(template.seller_ids), 2)
        self.assertEqual(row_b.price, 85.0)

    def test_supplier_price_keeps_template_row_of_multi_variant_product(self):
        template, variant_a, variant_b = self._variants()
        shared = self.env["product.supplierinfo"].create(
            {"partner_id": self.vendor.id, "product_tmpl_id": template.id, "product_code": "SHARED", "price": 10.0}
        )
        self.Wizard._update_supplier_price(self.vendor, variant_b, "CODE-B", 80.0, "RON")
        self.assertRecordValues(shared, [{"product_id": False, "product_code": "SHARED", "price": 10.0}])
        self.assertEqual(template.seller_ids.filtered("product_id").product_id, variant_b)

    def test_supplier_price_without_code_keeps_existing_code(self):
        product = self.env["product.product"].create({"name": "UBL Code Kept Product"})
        row = self.env["product.supplierinfo"].create(
            {
                "partner_id": self.vendor.id,
                "product_tmpl_id": product.product_tmpl_id.id,
                "product_code": "KEEP-1",
                "price": 10.0,
            }
        )
        self.Wizard._update_supplier_price(self.vendor, product, "", 12.0, "RON")
        self.assertRecordValues(row, [{"product_code": "KEEP-1", "price": 12.0}])

    def test_supplier_price_keeps_other_company_row(self):
        product = self.env["product.product"].create({"name": "UBL Company Product"})
        other = self.env["product.supplierinfo"].create(
            {
                "partner_id": self.vendor.id,
                "product_tmpl_id": product.product_tmpl_id.id,
                "price": 10.0,
                "company_id": self.company_b.id,
            }
        )
        self.Wizard.with_company(self.company)._update_supplier_price(self.vendor, product, "C-1", 20.0, "RON")
        self.assertEqual(other.price, 10.0)
        own = product.seller_ids - other
        self.assertRecordValues(own, [{"company_id": self.company.id, "price": 20.0}])

    # ------------------------------------------------------------------
    # SET unit code (#3440)
    # ------------------------------------------------------------------
    def test_set_unit_code_uses_a_set_unit_when_defined(self):
        wiz = self.Wizard.new({})
        # no standard set unit: unknown without fallback, Units with fallback
        if not self.env["uom.uom"].search([("name", "=ilike", "set")]):
            self.assertFalse(wiz._uom_from_code("SET", fallback=False))
            self.assertEqual(wiz._uom_from_code("SET"), self.unit)
        uom_set = self.env["uom.uom"].create({"name": "Set", "relative_factor": 1.0, "relative_uom_id": self.unit.id})
        self.assertEqual(wiz._uom_from_code("SET", fallback=False), uom_set)
        self.assertEqual(wiz._uom_from_code("set"), uom_set)

    def test_unknown_unit_code_is_reported(self):
        product = self.env["product.product"].create({"name": "UBL Unknown Unit", "default_code": "UNK-1"})
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "company_id": self.company.id,
                "order_line": [(0, 0, {"product_id": product.id, "product_qty": 1.0, "price_unit": 1.0})],
            }
        )
        xml = _xml_invoice(
            invoice_id="",
            order_ref=po.name,
            supplier_vat=self.vendor.vat,
            supplier_name=self.vendor.name,
            lines=[
                {"code": "UNK-1", "name": product.name, "qty": "2", "price": "3", "line_total": "6", "unit_code": "XYZ"}
            ],
        )
        wiz = self.Wizard.with_context(active_model="purchase.order", active_id=po.id).create(
            {"data_file": b64encode(xml), "update_prices": False, "create_missing_products": False}
        )
        wiz.action_import()
        self.assertAlmostEqual(po.order_line.product_qty, 2.0)
        self.assertIn("unit XYZ of source line UNK-1 is not known", wiz.log)
