# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools.binary import BinaryBytes

from .test_ubl_import import _xml_invoice


@tagged("post_install", "-at_install")
class TestPurchaseUblImportUom(TransactionCase):
    """UBL-005: source quantities/prices are converted from the XML unitCode."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.uom_kg = cls.env.ref("uom.product_uom_kgm")
        cls.uom_gram = cls.env.ref("uom.product_uom_gram")
        cls.vendor = cls.env["res.partner"].create({"name": "UoM Vendor SRL", "vat": "RO987654321", "supplier_rank": 1})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Flour",
                "default_code": "UOM-FLOUR",
                "is_storable": True,
                "purchase_ok": True,
                "uom_id": cls.uom_kg.id,
            }
        )

    def _po(self, lines, confirm=False):
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "company_id": self.company.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_qty": qty,
                            "price_unit": price,
                            "uom_id": uom.id,
                            "date_planned": "2025-01-01 00:00:00",
                        },
                    )
                    for product, qty, price, uom in lines
                ],
            }
        )
        if confirm:
            po.button_confirm()
        return po

    def _import(self, po, lines, validate_receipt=False, update_prices=True):
        xml = _xml_invoice(
            invoice_id="",
            order_ref=po.name,
            supplier_vat=self.vendor.vat,
            supplier_name=self.vendor.name,
            lines=lines,
        )
        wiz = (
            self.env["purchase.ubl.import.wizard"]
            .with_context(active_model="purchase.order", active_id=po.id)
            .create(
                {
                    "data_file": BinaryBytes(xml),
                    "filename": "uom.xml",
                    "update_prices": update_prices,
                    "create_bill": False,
                    "validate_receipt": validate_receipt,
                    "create_missing_products": False,
                }
            )
        )
        wiz.action_import()
        return wiz

    def _gram_line(self, qty="1000", price="0.01", unit_code="GRM"):
        return {
            "code": "UOM-FLOUR",
            "name": "Flour",
            "qty": qty,
            "price": price,
            "line_total": "10",
            "unit_code": unit_code,
        }

    def test_existing_order_line_converted_to_order_unit(self):
        po = self._po([(self.product, 2.0, 9.0, self.uom_kg)])
        seller = self.env["product.supplierinfo"].create(
            {
                "partner_id": self.vendor.id,
                "product_tmpl_id": self.product.product_tmpl_id.id,
                "uom_id": self.uom_kg.id,
                "price": 9.0,
            }
        )
        self._import(po, [self._gram_line()])

        line = po.order_line
        self.assertEqual(line.uom_id, self.uom_kg)
        self.assertAlmostEqual(line.product_qty, 1.0)
        self.assertAlmostEqual(line.price_unit, 10.0)
        self.assertAlmostEqual(po.amount_untaxed, 10.0)
        # the vendor price stays in the unit of the pricelist row
        self.assertEqual(seller.uom_id, self.uom_kg)
        self.assertAlmostEqual(seller.price, 10.0)

    def test_new_line_and_new_vendor_price_keep_source_unit(self):
        # an order without lines: the product is matched globally and added as a new line
        po = self._po([])
        self._import(po, [self._gram_line(qty="500", price="0.02")])

        line = po.order_line.filtered(lambda pol: pol.product_id == self.product)
        self.assertRecordValues(line, [{"uom_id": self.uom_gram.id, "product_qty": 500.0, "price_unit": 0.02}])
        seller = self.env["product.supplierinfo"].search(
            [("partner_id", "=", self.vendor.id), ("product_tmpl_id", "=", self.product.product_tmpl_id.id)]
        )
        self.assertRecordValues(seller, [{"uom_id": self.uom_gram.id, "price": 0.02}])

    def test_receipt_quantity_converted_to_move_unit(self):
        po = self._po([(self.product, 1.0, 10.0, self.uom_kg)], confirm=True)
        picking = po.picking_ids
        self._import(po, [self._gram_line()], validate_receipt=True, update_prices=False)

        self.assertEqual(picking.state, "done")
        self.assertEqual(picking.move_ids.uom_id, self.uom_kg)
        self.assertAlmostEqual(picking.move_ids.quantity, 1.0)
        self.assertAlmostEqual(po.order_line.qty_received, 1.0)

    def test_incompatible_unit_is_not_converted_and_reported(self):
        po = self._po([(self.product, 2.0, 9.0, self.uom_kg)])
        wiz = self._import(po, [self._gram_line(qty="3", price="4", unit_code="C62")], update_prices=False)

        self.assertAlmostEqual(po.order_line.product_qty, 3.0)
        self.assertAlmostEqual(po.order_line.price_unit, 4.0)
        self.assertIn("is not compatible with", wiz.log)

    def test_uom_from_code_without_fallback(self):
        wiz = self.env["purchase.ubl.import.wizard"].new({})
        self.assertFalse(wiz._uom_from_code("NOT-A-UNIT", fallback=False))
        self.assertEqual(wiz._uom_from_code("MLT"), self.env.ref("uom.product_uom_milliliter"))
        self.assertEqual(wiz._uom_from_code("MMT"), self.env.ref("uom.product_uom_millimeter"))
