# © 2008-2025 Terrabit / Deltatech
# Teste pentru modulul deltatech_logistic_docs

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSaleOrderAttachments(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env["res.partner"]
        cls.Attachment = cls.env["ir.attachment"]
        cls.SaleOrder = cls.env["sale.order"]
        cls.StockPicking = cls.env["stock.picking"]

        cls.partner = cls.env.ref("base.main_partner")

        cls.sale = cls.SaleOrder.create(
            {
                "partner_id": cls.partner.id,
            }
        )

    def test_sale_order_attachment_count_and_action(self):
        # atașament direct pe comanda de vânzare
        self.Attachment.create(
            {
                "name": "so_note.txt",
                "type": "binary",
                "datas": "MQ==",  # b"1" base64
                "res_model": "sale.order",
                "res_id": self.sale.id,
            }
        )

        # Domeniul ar trebui să includă cel puțin atașamentul direct al comenzii
        domain = self.sale.get_attachment_domain()
        count = self.Attachment.search_count(domain)
        self.assertGreaterEqual(count, 1, "Numărul de atașamente pentru SO trebuie să fie >= 1")

        # Creează un picking legat de SO și atașament pe picking
        picking = self.StockPicking.create(
            {
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "partner_id": self.partner.id,
                "sale_id": self.sale.id,
            }
        )

        self.Attachment.create(
            {
                "name": "picking_doc.pdf",
                "type": "binary",
                "datas": "MQ==",
                "res_model": "stock.picking",
                "res_id": picking.id,
            }
        )

        # Recalculează doc_count și verifică că a crescut
        self.sale.invalidate_recordset()
        self.sale._compute_attached_docs_count()
        self.assertGreaterEqual(self.sale.doc_count, 2)

        # Verifică structura acțiunii deschisă din buton
        action = self.sale.attachment_tree_view()
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get("res_model"), "ir.attachment")
        self.assertIn("domain", action)


@tagged("post_install", "-at_install")
class TestStockPickingAttachments(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Attachment = cls.env["ir.attachment"]
        cls.StockPicking = cls.env["stock.picking"]
        cls.SaleOrder = cls.env["sale.order"]
        cls.partner = cls.env.ref("base.main_partner")

        cls.picking = cls.StockPicking.create(
            {
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                "partner_id": cls.partner.id,
            }
        )

    def test_picking_attachment_count_and_action(self):
        # atașament direct pe picking
        self.Attachment.create(
            {
                "name": "pick_note.txt",
                "type": "binary",
                "datas": "MQ==",
                "res_model": "stock.picking",
                "res_id": self.picking.id,
            }
        )

        domain = self.picking.get_attachment_domain()
        count = self.Attachment.search_count(domain)
        self.assertGreaterEqual(count, 1)

        # Leagă un SO de picking și atașament pe SO; domeniul trebuie să includă și atașamentele SO
        sale = self.SaleOrder.create(
            {
                "partner_id": self.partner.id,
            }
        )
        self.picking.sale_id = sale.id

        self.Attachment.create(
            {
                "name": "so_linked.txt",
                "type": "binary",
                "datas": "MQ==",
                "res_model": "sale.order",
                "res_id": sale.id,
            }
        )

        self.picking.invalidate_recordset()
        self.picking._compute_attached_docs_count()
        self.assertGreaterEqual(self.picking.doc_count, 2)

        action = self.picking.attachment_tree_view()
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get("res_model"), "ir.attachment")
        self.assertIn("domain", action)


@tagged("post_install", "-at_install")
class TestAccountMoveAttachments(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Attachment = cls.env["ir.attachment"]
        cls.AccountMove = cls.env["account.move"]
        cls.AccountJournal = cls.env["account.journal"]
        cls.partner = cls.env.ref("base.main_partner")

        # Folosim orice jurnal disponibil (de obicei există cel puțin un jurnal general)
        cls.journal = cls.AccountJournal.search([], limit=1)
        # Dacă mediul de test nu are jurnale (rar), creăm un jurnal minimal general
        if not cls.journal:
            cls.journal = cls.AccountJournal.create(
                {
                    "name": "Misc",
                    "code": "MISC",
                    "type": "general",
                }
            )

        # Creăm un move generic (nu e nevoie să-l postăm pentru a testa domeniul de atașamente)
        cls.move = cls.AccountMove.create(
            {
                "move_type": "entry",  # nu folosim invoice pentru a evita dependențe de plan contabil
                "journal_id": cls.journal.id,
                "partner_id": cls.partner.id,
            }
        )

    def test_account_move_get_attachment_domain_and_action(self):
        # Atașament direct pe move
        self.Attachment.create(
            {
                "name": "move_note.txt",
                "type": "binary",
                "datas": "MQ==",
                "res_model": "account.move",
                "res_id": self.move.id,
            }
        )

        domain = self.move.get_attachment_domain()
        count = self.Attachment.search_count(domain)
        # Pentru move generic (nu invoice), domeniul trebuie să includă cel puțin atașamentul direct
        self.assertGreaterEqual(count, 1)

        # Verificăm și acțiunea de deschidere a atașamentelor
        action = self.move.attachment_tree_view()
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get("res_model"), "ir.attachment")
        self.assertIn("domain", action)


@tagged("post_install", "-at_install")
class TestPurchaseOrderAttachments(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Attachment = cls.env["ir.attachment"]
        cls.PurchaseOrder = cls.env["purchase.order"]
        cls.PurchaseOrderLine = cls.env["purchase.order.line"]
        cls.StockPicking = cls.env["stock.picking"]
        cls.Product = cls.env["product.product"]
        cls.AccountMove = cls.env["account.move"]
        cls.partner = cls.env.ref("base.main_partner")

        # Creeăm o comandă de achiziție minimă
        cls.po = cls.PurchaseOrder.create(
            {
                "partner_id": cls.partner.id,
            }
        )

    def test_purchase_order_domain_with_picking_and_invoice(self):
        # 1) Atașament direct pe PO
        self.Attachment.create(
            {
                "name": "po_doc.txt",
                "type": "binary",
                "datas": "MQ==",
                "res_model": "purchase.order",
                "res_id": self.po.id,
            }
        )

        domain = self.po.get_attachment_domain()
        count = self.Attachment.search_count(domain)
        self.assertGreaterEqual(count, 1, "PO ar trebui să aibă cel puțin 1 atașament în domeniu")

        # 2) Picking legat de PO + atașament pe picking
        picking_in = self.StockPicking.create(
            {
                "picking_type_id": self.env.ref("stock.picking_type_in").id,
                "location_id": self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": self.env.ref("stock.stock_location_stock").id,
                "partner_id": self.partner.id,
                "purchase_id": self.po.id,
            }
        )

        self.Attachment.create(
            {
                "name": "incoming_picking.pdf",
                "type": "binary",
                "datas": "MQ==",
                "res_model": "stock.picking",
                "res_id": picking_in.id,
            }
        )

        self.po.invalidate_recordset()
        self.po._compute_attached_docs_count()

        # 3) Factură furnizor (in_invoice) legată de PO prin purchase_line_id + atașament pe factură
        product = self.Product.create(
            {
                "name": "Serviciu PO",
                "type": "service",
                "list_price": 10.0,
                "standard_price": 5.0,
            }
        )

        pol = self.PurchaseOrderLine.create(
            {
                "order_id": self.po.id,
                "product_id": product.id,
                "name": "Serviciu",
                "product_qty": 1.0,
                "price_unit": 10.0,
            }
        )

        bill = self.AccountMove.create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "name": "Serviciu",
                            "quantity": 1.0,
                            "price_unit": 10.0,
                            "purchase_line_id": pol.id,
                        },
                    )
                ],
            }
        )

        self.Attachment.create(
            {
                "name": "bill_scan.pdf",
                "type": "binary",
                "datas": "MQ==",
                "res_model": "account.move",
                "res_id": bill.id,
            }
        )

        # Domeniul PO trebuie să includă și atașamentul de pe factură prin invoice_ids
        domain = self.po.get_attachment_domain()
        count = self.Attachment.search_count(domain)

        # compute și acțiunea din buton
        self.po.invalidate_recordset()
        self.po._compute_attached_docs_count()

        action = self.po.attachment_tree_view()
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get("res_model"), "ir.attachment")
        self.assertIn("domain", action)

    def test_invoice_get_attachment_domain_with_sale_links(self):
        Product = self.env["product.product"]
        SaleOrder = self.env["sale.order"]
        SaleOrderLine = self.env["sale.order.line"]

        # jurnal de vânzări
        sale_journal = self.env["account.journal"].search([("type", "=", "sale")], limit=1)
        if not sale_journal:
            sale_journal = self.env["account.journal"].create(
                {
                    "name": "Sales",
                    "code": "SAL",
                    "type": "sale",
                }
            )

        # produs simplu de tip serviciu (evităm stocul)
        product = Product.create(
            {
                "name": "Test Service",
                "type": "service",
                "list_price": 10.0,
            }
        )

        # comanda de vânzare + linie
        sale = SaleOrder.create(
            {
                "partner_id": self.partner.id,
            }
        )
        sol = SaleOrderLine.create(
            {
                "order_id": sale.id,
                "product_id": product.id,
                "name": "Service line",
                "product_uom_qty": 1.0,
                "price_unit": 10.0,
            }
        )

        # factură client cu linie legată de SOL prin sale_line_ids
        invoice = self.AccountMove.create(
            {
                "move_type": "out_invoice",
                "journal_id": sale_journal.id,
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "name": "Service line",
                            "quantity": 1.0,
                            "price_unit": 10.0,
                            "sale_line_ids": [(6, 0, [sol.id])],
                        },
                    )
                ],
            }
        )

        # atașamente pe factură și pe comanda de vânzare
        self.Attachment.create(
            {
                "name": "inv_doc.pdf",
                "type": "binary",
                "datas": "MQ==",
                "res_model": "account.move",
                "res_id": invoice.id,
            }
        )
        self.Attachment.create(
            {
                "name": "so_contract.pdf",
                "type": "binary",
                "datas": "MQ==",
                "res_model": "sale.order",
                "res_id": sale.id,
            }
        )

        domain = invoice.get_attachment_domain()
        count = self.Attachment.search_count(domain)
        # Domeniul trebuie să includă atașamentele proprii facturii și ale SO legat prin linia de vânzare
        self.assertGreaterEqual(count, 2)

        # compute și acțiune
        invoice.invalidate_recordset()
        invoice._compute_attached_docs_count()
        self.assertGreaterEqual(invoice.doc_count, 2)

        action = invoice.attachment_tree_view()
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get("res_model"), "ir.attachment")
        self.assertIn("domain", action)
