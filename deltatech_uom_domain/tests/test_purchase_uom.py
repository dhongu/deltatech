# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import Form, tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestPurchaseUom(BaseCommon):
    """Cazul real: cherestea cumparata la mc si tinuta in stoc la bucata."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref("uom.group_uom")
        cls.uom_mc = cls.env["uom.uom"].create({"name": "mcub test"})
        cls.uom_buc = cls.env["uom.uom"].create(
            {"name": "buc [0.0384 mc] test", "relative_uom_id": cls.uom_mc.id, "relative_factor": 0.0384}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Furnizor cherestea"})
        cls.product = cls.env["product.product"].create(
            {"name": "Grinzi 8/8x6m", "uom_id": cls.uom_buc.id, "purchase_ok": True}
        )

    def _po_line_uom(self):
        po_form = Form(self.env["purchase.order"])
        po_form.partner_id = self.partner
        with po_form.order_line.new() as line:
            line.product_id = self.product
            uom = line.product_uom_id
        return uom

    def _add_seller(self, **vals):
        return self.env["product.supplierinfo"].create(
            {
                "partner_id": self.partner.id,
                "product_tmpl_id": self.product.product_tmpl_id.id,
                "product_uom_id": self.uom_mc.id,
                "price": 1300,
                **vals,
            }
        )

    def test_without_seller_uses_default_purchase_uom(self):
        """Produs nou, fara linie de furnizor: comanda ia UM implicita de achizitie."""
        self.product.purchase_uom_id = self.uom_mc
        self.assertEqual(self._po_line_uom(), self.uom_mc)

    def test_expired_seller_uses_default_purchase_uom(self):
        """Linia de furnizor expirata nu mai e folosita - standardul cadea pe UM produsului."""
        self._add_seller(date_end="2026-04-08")
        self.assertEqual(self._po_line_uom(), self.uom_buc, "fara campul nou, comportamentul standard")
        self.product.purchase_uom_id = self.uom_mc
        self.assertEqual(self._po_line_uom(), self.uom_mc)

    def test_purchase_uom_wins_over_old_seller(self):
        """O linie de furnizor veche, ramasa in bucati, nu mai impune UM pe comanda."""
        self._add_seller(product_uom_id=self.uom_buc.id)
        self.product.purchase_uom_id = self.uom_mc
        self.assertEqual(self._po_line_uom(), self.uom_mc)

    def test_po_line_domain_restricted_to_purchase_uom(self):
        self.product.purchase_uom_id = self.uom_mc
        order = self.env["purchase.order"].create(
            {"partner_id": self.partner.id, "order_line": [Command.create({"product_id": self.product.id})]}
        )
        self.assertEqual(order.order_line.allowed_uom_ids, self.uom_mc)

    def test_seller_takes_purchase_uom(self):
        """Cazul t1754: linia de furnizor noua iesea in UM produsului (bucati)."""
        self.product.purchase_uom_id = self.uom_mc
        seller = self.env["product.supplierinfo"].create(
            {"partner_id": self.partner.id, "product_tmpl_id": self.product.product_tmpl_id.id, "price": 1300}
        )
        self.assertEqual(seller.product_uom_id, self.uom_mc)
        self.assertEqual(seller.allowed_uom_ids, self.uom_mc)

    def test_seller_without_purchase_uom_keeps_tree_domain(self):
        seller = self._add_seller()
        self.assertIn(self.uom_mc, seller.allowed_uom_ids)
        self.assertIn(self.uom_buc, seller.allowed_uom_ids)

    def test_seller_form_takes_purchase_uom(self):
        """Din formularul produsului, linia de furnizor noua ia UM de achizitie."""
        self.product.purchase_uom_id = self.uom_mc
        with Form(self.product.product_tmpl_id) as tmpl_form, tmpl_form.seller_ids.new() as seller:
            seller.partner_id = self.partner
            self.assertEqual(seller.product_uom_id, self.uom_mc)

    def test_without_default_purchase_uom_keeps_standard(self):
        self.assertEqual(self._po_line_uom(), self.uom_buc)

    def test_allowed_purchase_uoms_same_tree(self):
        uom_kg = self.env.ref("uom.product_uom_kgm")
        allowed = self.product.product_tmpl_id.purchase_allowed_uom_ids
        self.assertIn(self.uom_mc, allowed)
        self.assertIn(self.uom_buc, allowed)
        self.assertNotIn(uom_kg, allowed)

    def test_incompatible_default_purchase_uom_rejected(self):
        """Domeniul din formular nu acopera importul sau RPC-ul."""
        with self.assertRaises(ValidationError):
            self.product.purchase_uom_id = self.env.ref("uom.product_uom_kgm")
