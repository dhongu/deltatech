# © 2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturile fișei consultant „Semnături e-mail": RO pentru fișă, EN pentru USAGE.md.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_mail_signature,deltatech_doc_screenshots \
#       --test-tags=/deltatech_mail_signature:TestMailSignatureScreenshots --stop-after-init
import io
import unittest

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

BODY = """
<table style="font-family: Arial, sans-serif; font-size: 13px; color: #333;"><tbody><tr>
<td style="padding-right: 14px;"><img src="/web/image/%(logo)s" width="120"/></td>
<td>
<p style="margin: 0;"><b>{{name}}</b> · <span style="color: #017e84;">{{job_title}}</span></p>
<p style="margin: 0;">Tel: {{phone}}</p>
<p style="margin: 0;"><a href="mailto:{{email}}">{{email}}</a></p>
<p style="margin: 6px 0 0 0;"><b>{{company}}</b> · CUI {{company_vat}}</p>
<p style="margin: 0;">{{company_address}}</p>
</td></tr></tbody></table>
"""


def _logo():
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (240, 90), "#017e84")
    ImageDraw.Draw(image).text((20, 26), "DEMO SRL", fill="white", font_size=34)
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


@tagged("-at_install", "post_install", "fise_screenshots")
class TestMailSignatureScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_mail_signature"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        env = cls.env
        company = cls.prepare_ro_company(name="Demo Semnături SRL")
        company.website = "www.demo-semnaturi.ro"
        env["mail.signature.template"].search([]).unlink()
        logo = env["ir.attachment"].create(
            {
                "name": "logo.png",
                "raw": _logo(),
                "mimetype": "image/png",
                "res_model": "mail.signature.template",
                "res_id": 0,
            }
        )
        cls.template = env["mail.signature.template"].create(
            {"name": "Semnătura companiei", "company_id": company.id, "body_html": BODY % {"logo": logo.id}}
        )
        cls.user = env["res.users"].create(
            {
                "name": "Maria Ionescu",
                "login": "maria.ionescu@demo-semnaturi.ro",
                "email": "maria.ionescu@demo-semnaturi.ro",
                "lang": "ro_RO",
                "company_id": company.id,
                "company_ids": [(6, 0, company.ids)],
            }
        )
        cls.user.partner_id.write({"function": "Director vânzări", "phone": "+40 722 123 456"})
        cls.template.action_generate_signatures()
        cls.admin = env.ref("base.user_admin")
        cls.admin.write(
            {"name": "Andrei Popescu", "email": "andrei.popescu@demo-semnaturi.ro", "company_id": company.id}
        )
        cls.admin.partner_id.write({"function": "Administrator", "phone": "+40 21 123 4567"})
        cls.admin.action_regenerate_signature()

    def _shots(self):
        env = self.env
        act_tpl = env.ref("deltatech_mail_signature.mail_signature_template_action").id
        act_users = env.ref("base.action_res_users").id
        act_my = env.ref("base.action_res_users_my").id
        return [
            # 1. lista șabloanelor
            {
                "url": f"action={act_tpl}&view_type=list",
                "name": "01_lista_sabloane.png",
                "wait": ".o_list_view",
                "settle": 1500,
            },
            # 2. șablonul: corpul scris în editor, cu logo și câmpuri
            {
                "url": f"action={act_tpl}&id={self.template.id}&model=mail.signature.template&view_type=form",
                "name": "02_formular_sablon.png",
                "wait": ".o_form_view",
                "settle": 2500,
                "full": True,
            },
            # 3. câmpurile disponibile
            {
                "url": f"action={act_tpl}&id={self.template.id}&model=mail.signature.template&view_type=form",
                "name": "03_campuri_disponibile.png",
                "wait": ".o_form_view",
                "click_tab": "Câmpuri disponibile",
                "settle": 1500,
            },
            # 4. semnătura generată pentru un utilizator
            {
                "url": f"action={act_users}&id={self.user.id}&model=res.users&view_type=form",
                "name": "04_semnatura_utilizator.png",
                "wait": ".o_form_view",
                "click_tab": "Preferințe",
                "settle": 2500,
                "full": True,
            },
            # 5. preferințele utilizatorului: butonul Regenerează semnătura mea
            {
                "url": f"action={act_my}&id={self.admin.id}&model=res.users&view_type=form",
                "name": "05_preferinte_utilizator.png",
                "wait": ".o_form_view",
                "settle": 2500,
                "full": True,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), hide_systray=True, viewport=(1400, 900))

    def test_capture_usage(self):
        shots = self._shots()
        shots[2]["click_tab"] = "Available fields"
        shots[3]["click_tab"] = "Preferences"
        self.capture_screenshots(shots, hide_systray=True, viewport=(1400, 900), lang="en_US")
