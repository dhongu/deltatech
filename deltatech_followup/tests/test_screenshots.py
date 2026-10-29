# Copyright (C) 2026 Terrabit
# License OPL-1 (https://www.odoo.com/documentation/user/legal/licenses/licenses.html)
#
# Capturi de ecran pentru fișa consultant „Reamintiri automate pentru facturile clienților" — generate în RO.
#
# Seedează doi clienți bifați pentru followup, cu câte o factură scadentă peste două zile: una de
# 2.380 lei (reamintirea pleacă) și una de 0,50 lei (sub marja de 1 leu: rămâne doar nota internă).
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i l10n_ro,deltatech_followup,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestFollowupScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_followup"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Comerț SRL")
        env = cls.env
        company = env.company
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [(4, company.id)], "company_id": company.id, "name": "Maria Ionescu"})
        admin.group_ids += env.ref("deltatech_followup.group_manage_followups")
        env.user.sudo().name = "Maria Ionescu"
        today = fields.Date.context_today(env["account.invoice.followup"])

        partner = env["res.partner"]
        cls.client = partner.create(
            {
                "name": "Alfa Distribuție SRL",
                "is_company": True,
                "email": "contabilitate@alfa-distributie.example",
                "lang": "ro_RO",
                "send_followup": True,
            }
        )
        cls.small_client = partner.create(
            {
                "name": "Beta Papetărie SRL",
                "is_company": True,
                "email": "office@beta-papetarie.example",
                "lang": "ro_RO",
                "send_followup": True,
            }
        )

        def invoice(customer, amount, number_days):
            move = env["account.move"].create(
                {
                    "move_type": "out_invoice",
                    "partner_id": customer.id,
                    "invoice_date": today - relativedelta(days=number_days),
                    "invoice_date_due": today + relativedelta(days=2),
                    "invoice_line_ids": [
                        (0, 0, {"name": "Servicii de mentenanță", "quantity": 1, "price_unit": amount, "tax_ids": []})
                    ],
                }
            )
            move.action_post()
            return move

        invoice(cls.client, 2380.0, 28)
        invoice(cls.small_client, 0.5, 28)

        cls.template = env["mail.template"].create(
            {
                "name": "Reamintire factură scadentă",
                "model_id": env.ref("base.model_res_partner").id,
                "subject": "Facturi cu scadență în două zile",
                "email_from": "contabilitate@demo-comert.example",
                "partner_to": "{{ object.id }}",
                "body_html": "<p>Bună ziua, ${object.name},</p>"
                "<p>Vă reamintim că următoarele facturi ajung la scadență în două zile:</p>"
                "[invoices]"
                "<p>Total de plată: $total_debit $currency.</p>"
                "<p>Vă mulțumim!</p>",
            }
        )
        cls.followup = (
            env["account.invoice.followup"]
            .sudo()
            .create(
                {
                    "name": "Facturi scadente peste 2 zile",
                    "code": "f-2",
                    "date_field": "Due date",
                    "relative_days": -2,
                    "match": "=",
                    "only_open": True,
                    "amount_margin": 1.0,
                    "mail_template": cls.template.id,
                    "invoice_html": "<p>Factura $number, scadentă la $date_due: $amount_due $currency</p>",
                }
            )
        )
        cls.cron = (
            env["ir.cron"]
            .sudo()
            .create(
                {
                    "name": "Reamintiri facturi clienți",
                    "model_id": env.ref("deltatech_followup.model_followup_send_wizard").id,
                    "state": "code",
                    "code": "model.run_followup()",
                    "interval_number": 1,
                    "interval_type": "days",
                    "user_id": admin.id,
                }
            )
        )
        cls.act_followups = env.ref("deltatech_followup.action_invoice_followup").id
        env.flush_all()

    def test_capture_fise(self):
        self.capture_screenshots(
            [
                # 1. Fișa clientului: bifa de followup
                {
                    "url": f"id={self.client.id}&model=res.partner&view_type=form",
                    "name": "01_partener_bifa_followup.png",
                    "wait": ".o_form_view",
                    "highlight": ["div[name='send_followup']"],
                    "settle": 1800,
                },
                # 2. Lista etapelor de followup
                {
                    "url": f"action={self.act_followups}&view_type=list",
                    "name": "02_lista_followups.png",
                    "wait": ".o_list_view .o_data_row",
                    "settle": 1500,
                },
                # 3. Formularul unei etape
                {
                    "url": f"id={self.followup.id}&model=account.invoice.followup&view_type=form",
                    "name": "03_formular_followup.png",
                    "wait": ".o_form_view",
                    "highlight": [
                        "div[name='code']",
                        "div[name='match']",
                        "div[name='relative_days']",
                        "div[name='amount_margin']",
                        "div[name='mail_template']",
                    ],
                    "hide_chatter": True,
                    "settle": 1800,
                },
                # 4. Acțiunea programată care rulează followup-urile
                {
                    "url": f"id={self.cron.id}&model=ir.cron&view_type=form",
                    "name": "04_actiune_programata.png",
                    "wait": ".o_form_view",
                    "highlight": ["div[name='model_id']", "div[name='interval_number']"],
                    "settle": 1800,
                },
            ]
        )
        # Rulează etapa ca acțiunea programată
        self.env["followup.send.wizard"].sudo().with_context(lang="ro_RO").run_followup()
        self.env.flush_all()
        mail = self.env["mail.mail"].search(
            [("model", "=", "res.partner"), ("res_id", "=", self.client.id)], order="id desc", limit=1
        )
        self.assertTrue(mail, "Reamintirea trebuie să fie creată pentru clientul cu factura de 2.380 lei.")
        self.capture_screenshots(
            [
                # 5. E-mailul de reamintire, cu rândurile facturilor
                {
                    "url": f"id={mail.id}&model=mail.mail&view_type=form",
                    "name": "05_email_trimis.png",
                    "wait": ".o_form_view",
                    "settle": 1800,
                },
                # 6. Nota internă pentru factura sub marjă
                {
                    "url": f"id={self.small_client.id}&model=res.partner&view_type=form",
                    "name": "06_nota_marja.png",
                    "wait": ".o-mail-Message",
                    "hide_chatter": False,
                    "settle": 3000,
                },
            ]
        )
