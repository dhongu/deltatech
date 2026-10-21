# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.exceptions import AccessError, UserError
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestChangeUoM(TransactionCase):
    def setUp(self):
        super().setUp()
        self.uom_unit = self.env.ref("uom.product_uom_unit")
        self.uom_dozen = self.env.ref("uom.product_uom_dozen")
        self.uom_kgm = self.env.ref("uom.product_uom_kgm")
        self.uom_ton = self.env.ref("uom.product_uom_ton")
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.product = self.env["product.template"].create(
            {
                "name": "Test Product",
                "uom_id": self.uom_unit.id,
                "seller_ids": [(0, 0, {"partner_id": self.partner.id, "price": 10})],
            }
        )
        self.variant = self.product.product_variant_id

    def _create_orders(self):
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [(0, 0, {"product_id": self.variant.id, "product_uom_qty": 1})],
            }
        )
        purchase_order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [(0, 0, {"product_id": self.variant.id, "product_qty": 1})],
            }
        )
        return sale_order, purchase_order

    def _run_wizard(self, uom, purchase_uom=None):
        wizard = Form(self.env["product.change.uom"].with_context(active_id=self.product.id))
        wizard.uom_id = uom
        if purchase_uom is not None:
            wizard.purchase_uom_id = purchase_uom
        wizard = wizard.save()
        wizard.with_context(active_id=self.product.id).do_change()

    def test_wizard(self):
        sale_order, purchase_order = self._create_orders()
        self._run_wizard(self.uom_dozen)

        self.assertEqual(self.product.uom_id, self.uom_dozen)
        self.assertEqual(self.variant.uom_id, self.uom_dozen)
        self.assertFalse(self.product.purchase_uom_id)
        self.assertEqual(self.product.seller_ids.product_uom_id, self.uom_dozen)
        self.assertEqual(sale_order.order_line.product_uom_id, self.uom_dozen)
        self.assertEqual(purchase_order.order_line.product_uom_id, self.uom_dozen)

    def test_wizard_purchase_uom(self):
        """UM de achizitie din 18.0 (`uom_po_id`) e acum `purchase_uom_id` din deltatech_uom_domain."""
        self.product.purchase_uom_id = self.uom_dozen
        self.product.seller_ids.product_uom_id = self.uom_dozen
        sale_order, purchase_order = self._create_orders()
        self.assertEqual(purchase_order.order_line.product_uom_id, self.uom_dozen)

        wizard = Form(self.env["product.change.uom"].with_context(active_id=self.product.id))
        self.assertEqual(wizard.purchase_uom_id, self.uom_dozen)
        self._run_wizard(self.uom_kgm, self.uom_ton)

        self.assertEqual(self.product.uom_id, self.uom_kgm)
        self.assertEqual(self.product.purchase_uom_id, self.uom_ton)
        self.assertEqual(self.product.seller_ids.product_uom_id, self.uom_ton)
        self.assertEqual(sale_order.order_line.product_uom_id, self.uom_kgm)
        self.assertEqual(purchase_order.order_line.product_uom_id, self.uom_ton)

    def test_wizard_purchase_uom_on_bill(self):
        """Factura de furnizor a unei comenzi in unitatea de achizitie urmeaza comanda."""
        self.product.purchase_uom_id = self.uom_dozen
        self.product.seller_ids.product_uom_id = self.uom_dozen
        self.product.purchase_method = "purchase"
        _sale_order, purchase_order = self._create_orders()
        purchase_order.button_confirm()
        purchase_order.action_create_invoice()
        bill_line = purchase_order.invoice_ids.invoice_line_ids
        self.assertEqual(bill_line.product_uom_id, self.uom_dozen)

        self._run_wizard(self.uom_kgm, self.uom_ton)

        self.assertEqual(purchase_order.order_line.product_uom_id, self.uom_ton)
        self.assertEqual(bill_line.product_uom_id, self.uom_ton)
        # receptia ramane convertibila la noua unitate a produsului
        self.assertTrue(purchase_order.order_line.move_ids.product_uom._has_common_reference(self.uom_kgm))

    def test_wizard_purchase_uom_cleared(self):
        """UM de achizitie din alt arbore decat noua UM a produsului se goleste."""
        self.product.purchase_uom_id = self.uom_dozen
        wizard = Form(self.env["product.change.uom"].with_context(active_id=self.product.id))
        wizard.uom_id = self.uom_kgm
        self.assertFalse(wizard.purchase_uom_id)

    def test_wizard_requires_group(self):
        """Doar utilizatorii din grupul *Allow to change unit of measure* pot schimba UM."""
        user = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_change_uom_user",
                "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )
        with self.assertRaises(AccessError):
            self.env["product.change.uom"].with_user(user).create({"uom_id": self.uom_dozen.id})
        wizard = self.env["product.change.uom"].create({"uom_id": self.uom_dozen.id})
        with self.assertRaises(AccessError):
            wizard.with_user(user).with_context(active_id=self.product.id).do_change()
        self.assertEqual(self.product.uom_id, self.uom_unit)

    def test_admin_has_group(self):
        self.assertTrue(self.env.ref("base.user_admin").has_group("deltatech_change_uom.group_change_uom"))

    def test_wizard_incompatible_purchase_uom(self):
        wizard = self.env["product.change.uom"].create(
            {"uom_id": self.uom_kgm.id, "purchase_uom_id": self.uom_dozen.id}
        )
        with self.assertRaises(UserError):
            wizard.with_context(active_id=self.product.id).do_change()
