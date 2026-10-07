# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import SUPERUSER_ID, Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestUomDomain(AccountTestInvoicingCommon):
    """Baza de conturi vine din `AccountTestInvoicingCommon` - fara ea, o baza de test
    fara demo n-are jurnale si factura furnizor nu se poate crea."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_dozen = cls.env.ref("uom.product_uom_dozen")
        cls.uom_kg = cls.env.ref("uom.product_uom_kgm")
        # unitate creata "ca la client": exista in baza, dar nu e legata de niciun produs
        cls.uom_ten = cls.env["uom.uom"].create(
            {"name": "10 buc", "relative_uom_id": cls.uom_unit.id, "relative_factor": 10}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Furnizor Test UoM"})
        cls.product = cls.env["product.product"].create(
            {"name": "Produs in bucati", "uom_id": cls.uom_unit.id, "purchase_ok": True}
        )

    def _po_line(self):
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [Command.create({"product_id": self.product.id, "product_qty": 1})],
            }
        )
        return order.order_line

    def test_purchase_line_offers_convertible_uoms(self):
        """Unitatea exista in baza, nu e pe produs - standardul n-o ofera, modulul da."""
        line = self._po_line()
        self.assertFalse(self.product.uom_ids, "produsul nu trebuie sa aiba unitati suplimentare")
        self.assertIn(self.uom_ten, line.allowed_uom_ids)
        self.assertIn(self.uom_dozen, line.allowed_uom_ids)

    def test_purchase_line_keeps_incompatible_uoms_out(self):
        """Largirea se opreste la marginea arborelui: o conversie fara sens ramane blocata."""
        line = self._po_line()
        self.assertNotIn(self.uom_kg, line.allowed_uom_ids)

    def test_purchase_line_keeps_native_uoms(self):
        """Ce calculeaza standardul nu se pierde."""
        line = self._po_line()
        self.assertIn(self.product.uom_id, line.allowed_uom_ids)

    def test_purchase_line_keeps_seller_uom(self):
        """UM de pe linia de furnizor ramane in domeniu, chiar daca e din alt arbore.

        Modulul doar adauga peste `super()`: nu filtreaza ce a decis standardul.
        """
        product = self.env["product.product"].create(
            {
                "name": "Produs cu furnizor in kg",
                "uom_id": self.uom_unit.id,
                "purchase_ok": True,
                "seller_ids": [Command.create({"partner_id": self.partner.id, "uom_id": self.uom_kg.id})],
            }
        )
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [Command.create({"product_id": product.id, "product_qty": 1})],
            }
        )
        line = order.order_line
        self.assertIn(self.uom_kg, line.allowed_uom_ids)
        self.assertIn(self.uom_ten, line.allowed_uom_ids)

    def test_vendor_bill_line_offers_convertible_uoms(self):
        """Factura de achizitie preia UM de pe comanda, deci domeniul ei trebuie sa o accepte."""
        move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [Command.create({"product_id": self.product.id, "quantity": 1})],
            }
        )
        line = move.invoice_line_ids
        self.assertIn(self.uom_ten, line.allowed_uom_ids)
        self.assertNotIn(self.uom_kg, line.allowed_uom_ids)

    def test_line_without_product(self):
        """Liniile de sectiune/nota nu au produs - nu trebuie sa crape."""
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [Command.create({"display_type": "line_section", "name": "Sectiune", "product_qty": 0})],
            }
        )
        self.assertFalse(order.order_line.allowed_uom_ids)

    def test_customer_invoice_line_keeps_native_domain(self):
        """Facturile de vanzare pleaca la ANAF prin e-Factura: domeniul ramane cel standard.

        `uom.uom._get_unece_code()` cade pe 'C62' ("one/piece") pentru o unitate fara cod
        UNECE, deci o factura emisa in "10 buc" ar declara cantitatea 2 ca fiind bucati.
        """
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [Command.create({"product_id": self.product.id, "quantity": 1})],
            }
        )
        self.assertNotIn(self.uom_ten, move.invoice_line_ids.allowed_uom_ids)

    def test_supplierinfo_offers_only_convertible_uoms(self):
        """Pe linia de furnizor standardul nu are domeniu pe UM.

        Cazul real: "ml" (mililitru) ales ca UM de achizitie pentru un cablu in metri;
        conversia trece fara eroare si 22,5 m devin 22.500 ml pe cererea de oferta.
        """
        uom_meter = self.env.ref("uom.product_uom_meter")
        uom_ml = self.env.ref("uom.product_uom_milliliter")
        uom_mlin = self.env["uom.uom"].create({"name": "mlin.", "relative_uom_id": uom_meter.id, "relative_factor": 1})
        cable = self.env["product.product"].create({"name": "Cablu", "uom_id": uom_meter.id})
        seller = self.env["product.supplierinfo"].create(
            {"partner_id": self.partner.id, "product_tmpl_id": cable.product_tmpl_id.id, "price": 1}
        )
        self.assertEqual(seller.uom_id, uom_meter)
        self.assertIn(uom_meter, seller.allowed_uom_ids)
        self.assertIn(uom_mlin, seller.allowed_uom_ids)
        self.assertNotIn(uom_ml, seller.allowed_uom_ids)
        self.assertNotIn(self.uom_unit, seller.allowed_uom_ids)

    def test_supplierinfo_variant_and_packagings(self):
        """Linia pe varianta foloseste UM variantei; ambalajele produsului raman in lista.

        In 20.0 `_get_available_uoms()` intoarce ambalajele doar cu functia multi-UM
        activa (`uom.group_uom` pe superuser).
        """
        self.env["res.users"].browse(SUPERUSER_ID).group_ids |= self.env.ref("uom.group_uom")
        self.product.uom_ids = self.uom_kg
        seller = self.env["product.supplierinfo"].create(
            {
                "partner_id": self.partner.id,
                "product_tmpl_id": self.product.product_tmpl_id.id,
                "product_id": self.product.id,
                "price": 1,
            }
        )
        self.assertIn(self.uom_ten, seller.allowed_uom_ids)
        self.assertIn(self.uom_kg, seller.allowed_uom_ids, "ambalajul legat explicit de produs ramane")

    def test_supplierinfo_views_load_domain_field(self):
        """Campul din domeniu trebuie sa ajunga in vederi, altfel clientul web crapa.

        UM pe linia de furnizor e vizibila doar cu grupul `uom.group_uom`.
        """
        self.env.user.group_ids |= self.env.ref("uom.group_uom")
        for view_type in ("form", "list"):
            arch = self.env["product.supplierinfo"].get_view(view_type=view_type)["arch"]
            self.assertIn('name="allowed_uom_ids"', arch, view_type)
