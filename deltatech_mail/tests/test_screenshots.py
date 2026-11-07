# © 2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturile fișei consultant „Substituții e-mail": RO pentru fișă, EN pentru USAGE.md.
#
# Seedează: o regulă de redirecționare a destinatarilor pentru Contacte, o regulă de expeditor
# generică, o regulă de înlocuire în corpul mesajelor și parametrul „Use Company Email" activ.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_mail,deltatech_doc_screenshots \
#       --test-tags=/deltatech_mail:TestMailScreenshots --stop-after-init
import unittest

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None


@tagged("-at_install", "post_install", "fise_screenshots")
class TestMailScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_mail"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Mesaje SRL")
        env = cls.env
        env["mail.substitution"].search([]).unlink()
        env["mail.body.substitution"].search([]).unlink()
        cls.receiver = env["mail.substitution"].create(
            {"name": "res.partner", "email": "test.mesaje@demo-mesaje.ro", "type": "receiver"}
        )
        env["mail.substitution"].create({"name": False, "email": "noreply@demo-mesaje.ro", "type": "sender"})
        cls.body_rule = env["mail.body.substitution"].create(
            {
                "name": "Semnătură veche",
                "body_part": "<p>Echipa Vânzări</p>",
                "substitution": "<p>Echipa Demo Mesaje SRL – vanzari@demo-mesaje.ro</p>",
            }
        )
        env["ir.config_parameter"].sudo().set_param("mail.use_company_email", "True")
        cls.param = env["ir.config_parameter"].sudo().search([("key", "=", "mail.use_company_email")], limit=1)

    def _shots(self):
        env = self.env
        act_sub = env.ref("deltatech_mail.action_mail_substitution").id
        act_body = env.ref("deltatech_mail.action_mail_body_substitution").id
        act_param = env.ref("base.ir_config_list_action").id
        return [
            # 1. lista regulilor de substituție a adreselor
            {
                "url": f"action={act_sub}&view_type=list&debug=1",
                "name": "01_lista_substitutii.png",
                "wait": ".o_list_view",
                "settle": 1500,
            },
            # 2. regula de redirecționare a destinatarilor pentru Contacte
            {
                "url": f"action={act_sub}&id={self.receiver.id}&model=mail.substitution&view_type=form&debug=1",
                "name": "02_formular_substitutie.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='name']", "div[name='email']", "div[name='type']"],
                "settle": 1500,
            },
            # 3. lista regulilor de înlocuire în corpul mesajelor
            {
                "url": f"action={act_body}&view_type=list&debug=1",
                "name": "03_lista_substitutii_corp.png",
                "wait": ".o_list_view",
                "settle": 1500,
            },
            # 4. regula de înlocuire: textul căutat și textul nou
            {
                "url": f"action={act_body}&id={self.body_rule.id}&model=mail.body.substitution&view_type=form&debug=1",
                "name": "04_formular_substitutie_corp.png",
                "wait": ".o_form_view",
                "settle": 2000,
                "full": True,
            },
            # 5. parametrul de sistem care folosește adresa companiei ca expeditor
            {
                "url": f"action={act_param}&id={self.param.id}&model=ir.config_parameter&view_type=form&debug=1",
                "name": "05_parametru_email_companie.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='key']", "div[name='value']"],
                "settle": 1500,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), hide_systray=True, viewport=(1400, 900))

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), hide_systray=True, viewport=(1400, 900), lang="en_US")
