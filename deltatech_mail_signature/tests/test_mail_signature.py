# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

import base64

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form, TransactionCase, tagged
from odoo.tools import mute_logger

from ..models.mail_signature_render import render

# 1x1 PNG
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


@tagged("post_install", "-at_install")
class TestMailSignature(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.Template = cls.env["mail.signature.template"]
        cls.Template.search([]).unlink()
        cls.company.write(
            {
                "website": "www.demo.ro",
                "phone": "021 111",
                "email": "office@demo.ro",
                "vat": "RO123",
                "street": "Str. Mare 1",
                "city": "Cluj",
            }
        )
        cls.template = cls.Template.create(
            {
                "name": "Company",
                "company_id": cls.company.id,
                "body_html": (
                    "<div><p><b>{{name}}</b></p><p>{{job_title}}</p><p>Tel: {{phone}}</p>"
                    "<p>{{company}}</p><p>{{company_address}}</p>"
                    '<p><a href="{{company_website}}">{{company_website}}</a></p></div>'
                ),
            }
        )
        cls.user = cls.env["res.users"].create(
            {"name": "Ana Pop", "login": "ana.pop@test.ro", "email": "ana.pop@test.ro", "company_id": cls.company.id}
        )
        cls.user.partner_id.write({"function": "Sales Manager", "phone": "0722 000 111"})

    def _admin_user(self):
        return self.env["res.users"].create(
            {
                "name": "Admin Two",
                "login": "admin2@test.ro",
                "group_ids": [(6, 0, [self.env.ref("base.group_system").id])],
            }
        )

    def test_01_render_fields(self):
        """CA1: name and company are filled in."""
        html = str(self.template._render_for(self.user))
        self.assertIn("Ana Pop", html)
        self.assertIn(self.company.name, html)
        self.assertIn("Sales Manager", html)
        self.assertIn("Tel: 0722 000 111", html)
        self.assertNotIn("{{", html)

    def test_02_html_escaped(self):
        """CA2: HTML in a value is text."""
        self.user.partner_id.function = "<script>alert(1)</script><b>boss</b>"
        html = str(self.template._render_for(self.user))
        self.assertNotIn("<script", html)
        self.assertNotIn("<b>boss", html)
        self.assertIn("&lt;", html)

    def test_03_empty_lines_removed(self):
        """CA3: a line with only empty fields disappears; a line with one filled field stays."""
        self.user.partner_id.write({"phone": False, "function": False})
        html = str(self.template._render_for(self.user))
        self.assertNotIn("Tel:", html)
        self.assertNotIn("<p></p>", html)
        self.assertIn("Ana Pop", html)
        mixed = self.Template.new({"company_id": self.company.id, "body_html": "<p>{{name}} / {{job_title}}</p>"})
        self.user.partner_id.function = False
        self.assertIn("Ana Pop /", str(mixed._render_for(self.user)))

    def test_04_unknown_field_refused(self):
        """CA4: unknown or malformed fields are refused and the error lists the valid ones."""
        other = self.env["res.company"].create({"name": "Other SRL"})
        with self.assertRaises(ValidationError) as cm:
            self.Template.create({"name": "x", "company_id": other.id, "body_html": "<p>{{nume}}</p>"})
        self.assertIn("{{nume}}", str(cm.exception))
        self.assertIn("{{job_title}}", str(cm.exception))
        with self.assertRaises(ValidationError):
            self.Template.create({"name": "x", "company_id": other.id, "body_html": "<p>{{name}</p>"})
        with self.assertRaises(ValidationError):
            self.template.body_html = "<p>{{ company_secret }}</p>"

    def test_05_href_safe(self):
        """CA5: website without scheme gets https; javascript: never reaches an href."""
        html = str(self.template._render_for(self.user))
        self.assertIn('href="http://www.demo.ro"', html)
        scheme_less = render('<a href="{{w}}">{{w}}</a>', {"w": "www.demo.ro"}, {"w": "https://www.demo.ro"})
        self.assertIn('href="https://www.demo.ro"', scheme_less)
        self.company.website = "javascript:alert(1)"
        html = str(self.template._render_for(self.user))
        self.assertNotIn("javascript", html.split("<a")[1].split(">")[0])
        self.company.website = "  JaVa\tScript:alert(1)"
        html = str(self.template._render_for(self.user))
        self.assertNotIn("href", html)
        self.company.website = "https://www.demo.ro"
        tpl = self.Template.new(
            {
                "company_id": self.company.id,
                "body_html": '<p><a href="https://{{company_website}}">x{{company_website}}</a></p>',
            }
        )
        self.assertIn('href="https://www.demo.ro"', str(tpl._render_for(self.user)))

    def test_06_one_active_per_company(self):
        """CA6: one active template per company."""
        with self.assertRaises(ValidationError), mute_logger("odoo.sql_db"):
            self.Template.create({"name": "Second", "company_id": self.company.id, "body_html": "<p>{{name}}</p>"})
        other = self.env["res.company"].create({"name": "Other SRL"})
        second = self.Template.create({"name": "Other", "company_id": other.id, "body_html": "<p>{{name}}</p>"})
        self.assertTrue(second.active)
        self.template.active = False
        again = self.Template.create({"name": "Second", "company_id": self.company.id, "body_html": "<p>{{name}}</p>"})
        self.assertTrue(again.active)

    def test_07_mass_generation(self):
        """CA7: all internal users of the company, nobody else."""
        other_company = self.env["res.company"].create({"name": "Other SRL"})
        elsewhere = self.env["res.users"].create(
            {
                "name": "Bob",
                "login": "bob@test.ro",
                "company_id": other_company.id,
                "company_ids": [(6, 0, other_company.ids)],
            }
        )
        portal = self.env["res.users"].create(
            {
                "name": "Portal",
                "login": "portal@test.ro",
                "company_id": self.company.id,
                "group_ids": [(6, 0, [self.env.ref("base.group_portal").id])],
            }
        )
        action = self.template.action_generate_signatures()
        self.assertEqual(action["tag"], "display_notification")
        self.assertTrue(self.user.mail_signature_generated)
        self.assertIn("Ana Pop", str(self.user.signature))
        self.assertIn("Sales Manager", str(self.user.signature))
        self.assertFalse(elsewhere.mail_signature_generated)
        self.assertFalse(portal.mail_signature_generated)
        self.assertNotIn("Sales Manager", str(elsewhere.signature))

    def test_08_regenerate_mine(self):
        """CA8: own signature replaced, also when hand-written; another user's refused."""
        self.user.write({"signature": "<p>my own</p>"})
        user = self.user.with_user(self.user)
        user.action_regenerate_signature()
        self.assertIn("Sales Manager", str(self.user.signature))
        self.assertTrue(self.user.mail_signature_generated)
        other = self.env["res.users"].create({"name": "Cip", "login": "cip@test.ro", "company_id": self.company.id})
        with self.assertRaises(AccessError):
            other.with_user(self.user).action_regenerate_signature()

    def test_09_manual_signature_kept(self):
        """CA9: hand-written signatures survive; a manual edit removes the mark."""
        self.user.write({"signature": "<p>hand made</p>"})
        self.assertFalse(self.user.mail_signature_generated)
        action = self.template.action_generate_signatures()
        self.assertIn("1", action["params"]["message"])
        self.assertIn("hand made", str(self.user.signature))
        self.user.partner_id.function = "Boss"
        self.assertIn("hand made", str(self.user.signature))
        self.user.action_regenerate_signature()
        self.assertTrue(self.user.mail_signature_generated)
        self.user.write({"signature": "<p>edited</p>"})
        self.assertFalse(self.user.mail_signature_generated)

    def test_10_auto_refresh(self):
        """CA10: a change of the data refreshes only generated signatures, and only with auto refresh on."""
        self.user.action_regenerate_signature()
        self.user.write({"function": "Director"})
        self.assertIn("Director", str(self.user.signature))
        self.user.partner_id.phone = "0799 999"
        self.assertIn("0799 999", str(self.user.signature))
        self.user.name = "Ana Maria Pop"
        self.assertIn("Ana Maria Pop", str(self.user.signature))
        self.assertTrue(self.user.mail_signature_generated)
        self.template.auto_refresh = False
        self.user.write({"function": "CEO"})
        self.assertNotIn("CEO", str(self.user.signature))

    def test_11_rights(self):
        """CA11: only administrators edit templates and generate for everybody."""
        with self.assertRaises(AccessError):
            self.template.with_user(self.user).write({"name": "hack"})
        with self.assertRaises(AccessError):
            self.Template.with_user(self.user).create({"name": "x", "body_html": "<p>x</p>"})
        with self.assertRaises(AccessError):
            self.template.with_user(self.user).unlink()
        with self.assertRaises(UserError):
            self.template.with_user(self.user).action_generate_signatures()
        admin = self._admin_user()
        self.template.with_user(admin).write({"name": "ok"})
        self.assertEqual(self.template.name, "ok")

    def test_12_images(self):
        """CA12: images are shared; limits of the mail client; data images refused."""
        attachment = self.env["ir.attachment"].create(
            {
                "name": "logo.png",
                "datas": base64.b64encode(PNG),
                "mimetype": "image/png",
                "res_model": self.Template._name,
                "res_id": 0,
            }
        )
        self.assertFalse(attachment.public)
        self.template.body_html = f'<p><img src="/web/image/{attachment.id}?access_token=abc"/></p><p>{{{{name}}}}</p>'
        self.assertTrue(attachment.public)
        self.assertEqual(attachment.res_id, self.template.id)
        html = str(self.template._render_for(self.user))
        self.assertIn(f"/web/image/{attachment.id}", html)
        with self.assertRaises(ValidationError):
            self.template.body_html = '<p><img src="data:image/png;base64,AAAA"/></p>'
        svg = self.env["ir.attachment"].create({"name": "x.svg", "raw": b"<svg/>", "mimetype": "image/svg+xml"})
        with self.assertRaises(ValidationError):
            self.template.body_html = f'<img src="/web/image/{svg.id}"/>'
        big = self.env["ir.attachment"].create(
            {"name": "big.png", "raw": PNG + b"0" * (301 * 1024), "mimetype": "image/png"}
        )
        with self.assertRaises(ValidationError):
            self.template.body_html = f'<img src="/web/image/{big.id}"/>'
        many = self.env["ir.attachment"].create(
            [{"name": f"{i}.png", "raw": PNG, "mimetype": "image/png"} for i in range(6)]
        )
        with self.assertRaises(ValidationError):
            self.template.body_html = "".join(f'<img src="/web/image/{a.id}"/>' for a in many)
        private = self.env["ir.attachment"].create(
            {
                "name": "p.png",
                "raw": PNG,
                "mimetype": "image/png",
                "res_model": "res.partner",
                "res_id": self.user.partner_id.id,
            }
        )
        with self.assertRaises(ValidationError):
            self.template.body_html = f'<img src="/web/image/{private.id}"/>'

    def test_13_multi_company_rule(self):
        """CA13: a user of company A does not see the template of company B."""
        other = self.env["res.company"].create({"name": "Other SRL"})
        hidden = self.Template.create({"name": "B", "company_id": other.id, "body_html": "<p>{{name}}</p>"})
        user = self.env["res.users"].create(
            {
                "name": "Dan",
                "login": "dan@test.ro",
                "company_id": self.company.id,
                "company_ids": [(6, 0, self.company.ids)],
            }
        )
        visible = self.Template.with_user(user).search([])
        self.assertIn(self.template, visible)
        self.assertNotIn(hidden, visible)

    def test_14_no_template(self):
        """Without an active template the action explains it."""
        self.template.active = False
        with self.assertRaises(UserError):
            self.user.action_regenerate_signature()

    def test_15_form_button_available(self):
        """The template form opens and saves."""
        self.template.active = False
        with Form(self.Template) as form:
            form.name = "Form template"
            form.body_html = "<p>{{name}}</p>"
        self.assertTrue(form.id)
        self.assertTrue(form.record.active)
