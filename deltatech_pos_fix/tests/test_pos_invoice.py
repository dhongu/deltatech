from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPosInvoice(TransactionCase):
    def setUp(self):
        super().setUp()
        self.PosOrder = self.env["pos.order"]
        self.tax_19 = self.env["account.tax"].create(
            {
                "name": "Tax 19%",
                "amount": 19,
                "amount_type": "percent",
                "price_include": True,
            }
        )
        self.tax_0 = self.env["account.tax"].create(
            {
                "name": "Tax 0%",
                "amount": 0,
                "amount_type": "percent",
                "price_include": False,
            }
        )
        self.fiscal_position = self.env["account.fiscal.position"].create(
            {
                "name": "B2B Reverse Charge",
                "tax_ids": [
                    (0, 0, {"tax_src_id": self.tax_19.id, "tax_dest_id": self.tax_0.id}),
                ],
            }
        )
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "is_storable": True,
                "list_price": 1190.0,
                "taxes_id": [(6, 0, [self.tax_19.id])],
            }
        )
        self.pos_config = self.env["pos.config"].create({"name": "Test POS"})
        self.pos_session = self.env["pos.session"].create({"config_id": self.pos_config.id})

    def test_pos_order_invoice_price_adaptation(self):
        # Cream o comandă POS cu prețul de 1190 (include TVA 19%, deci baza e 1000)
        pos_order = self.PosOrder.create(
            {
                "session_id": self.pos_session.id,
                "partner_id": self.env.ref("base.res_partner_1").id,
                "fiscal_position_id": self.fiscal_position.id,
                "lines": [
                    (
                        0,
                        0,
                        {
                            "name": "Test Line",
                            "product_id": self.product.id,
                            "qty": 1,
                            "price_unit": 1190.0,
                            "tax_ids": [(6, 0, [self.tax_19.id])],
                            "price_subtotal": 1000.0,
                            "price_subtotal_incl": 1190.0,
                        },
                    )
                ],
                "amount_tax": 0.0,  # După poziția fiscală, taxa e 0
                "amount_total": 1000.0,
                "amount_paid": 1000.0,
                "amount_return": 0.0,
            }
        )

        # Pregătim liniile de factură
        invoice_lines_vals = pos_order._prepare_invoice_lines()

        # Căutăm linia de produs în values (ignorăm eventualele note)
        product_line = next(
            l for l in invoice_lines_vals if isinstance(l, tuple) and l[2].get("product_id") == self.product.id
        )

        # Prețul unitar ar trebui să fie adaptat la 1000 (fără TVA)
        self.assertAlmostEqual(product_line[2]["price_unit"], 1000.0, places=2)
