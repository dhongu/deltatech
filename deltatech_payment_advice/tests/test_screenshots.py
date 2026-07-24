# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Aviz de plată către furnizori" — generate în timpul testelor,
# în limba RO, pe planul de conturi RO. Seedează: o companie RO cu jurnal de bancă (IBAN + bancă),
# un furnizor cu cod intern și e-mail, o factură furnizor postată, o plată și o plată în lot; apoi
# trimite avizul pe e-mail ca să poată fi pozat mesajul generat.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_payment_advice,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import base64
import io
import json
from urllib.parse import quote

from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPaymentAdviceScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_payment_advice"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Plăți SRL")  # RON, drepturi contabile + limba RO
        env = cls.env
        company = env.company
        env.ref("base.user_admin").write({"company_ids": [(4, company.id)], "company_id": company.id})
        cls._seed_company_logo(company)

        # Jurnal de bancă cu cont IBAN + bancă (apar în antetul avizului).
        bank = env["res.bank"].search([("name", "=", "Banca Transilvania")], limit=1) or env["res.bank"].create(
            {"name": "Banca Transilvania", "bic": "BTRLRO22"}
        )
        company_bank = env["res.partner.bank"].create(
            {
                "acc_number": "RO28BTRLRONCRT0CZ2318601",
                "partner_id": company.partner_id.id,
                "bank_id": bank.id,
            }
        )
        cls.bank_journal = env["account.journal"].search(
            [("type", "=", "bank"), ("company_id", "=", company.id)], limit=1
        )
        cls.bank_journal.bank_account_id = company_bank.id
        purchase_journal = env["account.journal"].search(
            [("type", "=", "purchase"), ("company_id", "=", company.id)], limit=1
        )
        expense = env["account.account"].search(
            [("account_type", "=", "expense"), ("company_ids", "in", [company.id])], order="code", limit=1
        )

        # Furnizor cu cod intern (apare ca „Contul dvs. la noi") și e-mail (pentru trimitere).
        cls.supplier = env["res.partner"].create(
            {
                "name": "Inedit Venture Investments SRL",
                "ref": "5394",
                "supplier_rank": 1,
                "street": "Str. G. Ghica Vodă nr. 3A",
                "zip": "700400",
                "city": "Iași",
                "country_id": env.ref("base.ro").id,
                "email": "furnizor@example.ro",
                "lang": "ro_RO",
            }
        )

        last_month = fields.Date.today() - relativedelta(months=1)
        bill_date = last_month.replace(day=7)
        cls.bill = env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": cls.supplier.id,
                "journal_id": purchase_journal.id,
                "invoice_date": bill_date,
                "invoice_date_due": bill_date + relativedelta(days=14),
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Servicii conform contract",
                            "account_id": expense.id,
                            "quantity": 1,
                            "price_unit": 16111.88,
                        }
                    )
                ],
            }
        )
        cls.bill.action_post()

        payment = (
            env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=cls.bill.ids)
            .create({"journal_id": cls.bank_journal.id})
            ._create_payments()
        )
        cls.batch = env["account.batch.payment"].create(
            {
                "journal_id": cls.bank_journal.id,
                "batch_type": "outbound",
                "payment_ids": [Command.set(payment.ids)],
            }
        )

        # Trimite avizul pe e-mail ca să existe mesajul generat de pozat (force_send=False).
        cls.batch.action_send_payment_advice()
        cls.mail = env["mail.mail"].search(
            [("model", "=", "account.batch.payment"), ("res_id", "=", cls.batch.id)], limit=1
        )

    @classmethod
    def _seed_company_logo(cls, company):
        """Pune o siglă simplă pe compania de test, ca antetul avizului să nu apară cu
        placeholder-ul „Your logo" într-un document destinat furnizorului."""
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            return
        img = Image.new("RGB", (260, 72), "#1a4d2e")
        ImageDraw.Draw(img).text((16, 30), company.name, fill="#ffffff")
        buf = io.BytesIO()
        img.save(buf, "PNG")
        company.logo = base64.b64encode(buf.getvalue())
        cls.env.flush_all()

    def _email_preview_html(self):
        """Previzualizare de tip client de e-mail a mesajului real generat (RO), pentru fișă."""
        mail = self.mail
        attachment = ", ".join(mail.attachment_ids.mapped("name")) or "—"
        return f"""<!DOCTYPE html><html><head><meta charset='utf-8'><style>
            body{{margin:0;padding:24px;background:#f3f4f6;
                 font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;}}
            .mail{{max-width:760px;margin:0 auto;background:#fff;border:1px solid #d1d5db;
                   border-radius:8px;overflow:hidden;}}
            .hdr{{padding:16px 20px;border-bottom:1px solid #e5e7eb;background:#fafafa;}}
            .subj{{font-size:17px;font-weight:700;color:#111827;margin-bottom:10px;}}
            .row{{font-size:13px;color:#374151;margin:3px 0;}}
            .row b{{color:#6b7280;font-weight:600;display:inline-block;width:64px;}}
            .att{{display:inline-block;margin-top:8px;padding:6px 12px;background:#eef2ff;
                  border:1px solid #c7d2fe;border-radius:6px;font-size:13px;color:#3730a3;}}
            .body{{padding:20px;font-size:14px;color:#1f2937;line-height:1.5;}}
        </style></head><body><div class='mail'>
            <div class='hdr'>
                <div class='subj'>{mail.subject}</div>
                <div class='row'><b>Către:</b> {mail.email_to}</div>
                <div class='row'><b>De la:</b> {mail.email_from}</div>
                <div class='att'>📎 {attachment}</div>
            </div>
            <div class='body'>{mail.body_html or ""}</div>
        </div></body></html>"""

    def test_capture_fise(self):
        # Randarea raportului prin /report/html trece prin regula multi-company a plății în lot;
        # transmitem compania de test în context ca înregistrarea să fie lizibilă în sesiune.
        report_ctx = quote(json.dumps({"lang": "ro_RO", "allowed_company_ids": [self.env.company.id]}))
        # Curăță ecranul pentru manual: ascunde zona de systray din navbar (iconuri irelevante
        # pentru fișă — developer mode, Web Studio, AI, notificări, activități) și elimină
        # bannerul Enterprise „bază de date expirată" (test19 e o bază neînregistrată). Ascunderea
        # se face prin <style> injectat, ca să reziste la re-randările OWL.
        hide_expired = (
            "var st=document.createElement('style');"
            "st.textContent='.o_menu_systray{display:none!important}';"
            "document.head.appendChild(st);"
            "document.querySelectorAll('.o_database_expiration_panel, .database_expiration_panel')"
            ".forEach(e=>e.remove());"
            "[...document.querySelectorAll('.alert')]"
            ".filter(e=>/expirat|expired|abonament/i.test(e.textContent||''))"
            ".forEach(e=>e.remove());"
        )
        self.capture_screenshots(
            [
                # 1. Formularul plății în lot, cu butonul „Trimite avizul de plată"
                {
                    "url": f"id={self.batch.id}&model=account.batch.payment&view_type=form",
                    "name": "01_plata_in_lot.png",
                    "wait": ".o_form_view",
                    "highlight": "button[name='action_send_payment_advice']",
                    "eval": hide_expired,
                    "settle": 2500,
                    "full": True,
                },
                # 2. Avizul de plată tipărit (PDF), randat HTML în limba furnizorului
                {
                    "path": (
                        "/report/html/deltatech_payment_advice.action_report_payment_advice/"
                        f"{self.batch.id}?context={report_ctx}"
                    ),
                    "name": "02_aviz_pdf.png",
                    "wait": "body",
                    "settle": 2500,
                    "full": True,
                },
                # 3. E-mailul cu avizul atașat, trimis furnizorului
                {
                    "html": self._email_preview_html(),
                    "name": "03_email_furnizor.png",
                    "full": True,
                },
            ],
            viewport=(1500, 1200),
        )
