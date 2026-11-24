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
<table style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: #1f3d2b; width: 440px; max-width: 100%%; border-collapse: collapse;"><tbody>
<tr><td colspan="2" style="padding: 0;"><img src="/web/image/%(banner)s" width="440" style="display: block; width: 100%%; border-radius: 14px 14px 0 0;"/></td></tr>
<tr>
<td style="padding: 18px 0 6px 16px; vertical-align: top;">
<p style="margin: 0 0 6px 0; font-size: 20px; font-weight: bold;">{{name}}</p>
<p style="margin: 0 0 4px 0; font-size: 14px; color: #6b7d70;">{{job_title}}</p>
<p style="margin: 0 0 4px 0; font-size: 14px; color: #6b7d70;">Tel: {{phone}}</p>
<p style="margin: 0;"><a href="mailto:{{email}}" style="color: #2d6e3a; font-weight: bold; text-decoration: none;">{{email}}</a></p>
</td>
<td style="padding: 18px 16px 6px 0; vertical-align: top; text-align: right;"><img src="/web/image/%(logo)s" width="110"/></td>
</tr>
<tr><td colspan="2" style="padding: 10px 16px;">
<table style="width: 100%%; background-color: #f5f2ea; border-radius: 12px; border-collapse: separate;"><tbody><tr>
<td style="padding: 14px 16px; vertical-align: middle;">
<p style="margin: 0 0 4px 0; font-size: 15px;"><b>{{company}}</b> <span style="color: #6b7d70;">&middot; utilaje agricole</span></p>
<p style="margin: 0; font-size: 13px; color: #6b7d70;">{{company_address}}</p>
</td>
<td style="padding: 14px 16px; text-align: right; vertical-align: middle;"><a href="{{company_website}}" style="background-color: #f8d84a; color: #1f3d2b; font-weight: bold; padding: 8px 12px; border-radius: 10px; text-decoration: none; white-space: nowrap;">Catalog online &rarr;</a></td>
</tr></tbody></table>
</td></tr>
<tr><td colspan="2" style="padding: 4px 16px 0 16px; font-size: 14px;"><a href="{{company_website}}" style="color: #2d6e3a; font-weight: bold; text-decoration: none;">{{company_website}}</a> <span style="color: #6b7d70;">&middot; Facebook &middot; Instagram &middot; TikTok &middot; YouTube</span></td></tr>
<tr><td colspan="2" style="padding: 10px 16px 16px 16px; font-size: 12px; color: #a3aea6;">
<p style="margin: 0 0 3px 0;">{{company}} &middot; CUI {{company_vat}}</p>
<p style="margin: 0;">Acest mesaj &#537;i eventualele ata&#537;amente sunt confiden&#539;iale &#537;i destinate exclusiv destinatarului.</p>
</td></tr>
</tbody></table>
"""

# deschide editorul pe toată înălțimea semnăturii (altfel se vede doar începutul)
EXPAND = """async () => {
    await new Promise((r) => setTimeout(r, 1500));
    const st = document.createElement('style');
    st.textContent = '.o_field_html .odoo-editor-editable, .o_field_html .o_readonly, .o_field_html .note-editable, ' +
        '.o_field_html .o-wysiwyg, .o_field_html .o_field_html_content, .o_field_html > div {height: auto !important; ' +
        'max-height: none !important; min-height: 0 !important; overflow: visible !important}';
    document.head.appendChild(st);
    for (const f of document.querySelectorAll('.o_field_html iframe')) {
        try { f.style.height = (f.contentDocument.documentElement.scrollHeight + 10) + 'px'; } catch (e) {}
    }
}"""

# în fereastra de preferințe (îngustă) semnătura se micșorează, ca să încapă întreagă lângă buton
EXPAND_ZOOM = """async () => {
    await new Promise((r) => setTimeout(r, 1500));
    const st = document.createElement('style');
    st.textContent = '.o_field_html .odoo-editor-editable, .o_field_html > div {height: auto !important; ' +
        'max-height: none !important; min-height: 0 !important; overflow: visible !important}';
    document.head.appendChild(st);
    for (const f of document.querySelectorAll('.o_field_html iframe')) {
        try {
            f.contentDocument.documentElement.style.zoom = '0.62';
            f.style.height = (f.contentDocument.documentElement.scrollHeight * 0.62 + 12) + 'px';
        } catch (e) {}
    }
    const el = document.querySelector('.o_field_html .odoo-editor-editable');
    if (el) { el.style.zoom = '0.62'; }
}"""


def _png(image):
    buffer = io.BytesIO()
    image.save(buffer, "PNG", optimize=True)
    return buffer.getvalue()


def _logo():
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (340, 110), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((6, 10, 96, 100), fill="#2d6e3a")
    draw.pieslice((6, 10, 96, 100), 180, 360, fill="#f8d84a")
    draw.text((112, 34), "Demo Agro", fill="#2d6e3a", font_size=44)
    return _png(image)


def _banner():
    from PIL import Image, ImageDraw

    width, height = 600, 120
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    for y in range(height):  # cer degrade
        t = y / height
        draw.line((0, y, width, y), fill=(int(222 - 60 * t), int(236 - 40 * t), int(248 - 80 * t)))
    draw.ellipse((470, 8, 550, 88), fill="#f8d84a")  # soare
    draw.ellipse((-80, 62, 420, 210), fill="#8cc08f")  # dealuri
    draw.ellipse((200, 78, 760, 230), fill="#3f8a46")
    for i in range(6):  # brazde
        draw.line((0, 118 - i * 4, width, 104 - i * 4), fill="#2d6e3a", width=1)
    draw.rounded_rectangle((60, 52, 130, 90), 8, fill="#2d6e3a")  # tractor
    draw.ellipse((100, 58, 146, 104), fill="#2d6e3a")
    draw.ellipse((112, 70, 134, 92), fill="#8cc08f")
    return _png(image)


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
        images = {}
        for key, raw in (("logo", _logo()), ("banner", _banner())):
            images[key] = (
                env["ir.attachment"]
                .create(
                    {
                        "name": f"{key}.png",
                        "raw": raw,
                        "mimetype": "image/png",
                        "res_model": "mail.signature.template",
                        "res_id": 0,
                    }
                )
                .id
            )
        cls.template = env["mail.signature.template"].create(
            {"name": "Semnătura companiei", "company_id": company.id, "body_html": BODY % images}
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
                "eval": EXPAND,
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
                "eval": EXPAND,
                "wait": ".o_form_view",
                "click_tab": "Preferințe",
                "settle": 2500,
                "full": True,
            },
            # 5. preferințele utilizatorului: butonul Regenerează semnătura mea
            {
                "url": f"action={act_my}&id={self.admin.id}&model=res.users&view_type=form",
                "name": "05_preferinte_utilizator.png",
                "eval": EXPAND_ZOOM,
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
