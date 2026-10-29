# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Rolul atributului de produs" — generate în timpul
# testelor, în limba RO, pe compania „Demo Atribute SRL".
#
# Modulul nu are roluri proprii: testul adaugă rolurile Soi / Calitate / Calibru, ca un
# modul care le-ar adăuga cu `selection_add` (ex. `inedit_apple_grading`). Seedează
# atributele Soi, Calitate și Calibru cu rolurile lor, plus Culoare fără rol. Ultima
# captură încearcă să dea rolul Soi și atributului Calibru, ca să arate refuzul.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_product_attribute_role,stock,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest
from unittest.mock import patch

from odoo import Command
from odoo.tests import tagged
from odoo.tools import mute_logger

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

ROLES = [("soi", "Soi"), ("calitate", "Calitate"), ("calibru", "Calibru")]

# alege rolul „Soi" pe atributul deschis și salvează, ca să apară refuzul
TAKE_ROLE = """async () => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    document.querySelector("div[name='attribute_role'] .o_select_menu_toggler").click();
    await sleep(800);
    [...document.querySelectorAll(".o_select_menu_item")].find((i) => i.textContent.trim() === "Soi").click();
    await sleep(800);
    document.querySelector(".o_form_button_save").click();
    await sleep(2000);
}"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestAttributeRoleScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_product_attribute_role"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        field = cls.env["product.attribute"]._fields["attribute_role"]
        selection = [*field.selection, *ROLES]
        cls.startClassPatcher(patch.object(field, "selection", selection))
        cls.startClassPatcher(patch.object(field, "_selection", dict(selection)))

        cls.prepare_ro_company(name="Demo Atribute SRL")
        env = cls.env
        admin = env.ref("base.user_admin")
        group = env.ref("product.group_product_variant")
        admin.group_ids = [Command.link(group.id)]
        env.user.group_ids = [Command.link(group.id)]

        Attribute = env["product.attribute"]
        Attribute.search([("attribute_role", "in", [role for role, _label in ROLES])]).attribute_role = False
        # atributele demo nefolosite („Legs", „Color"...) ar umple lista: le arhivăm
        Attribute.search([]).filtered(lambda a: not a.number_related_products).active = False

        def attribute(name, role, values, sequence):
            return Attribute.create(
                {
                    "name": name,
                    "sequence": sequence,
                    "create_variant": "always",
                    "attribute_role": role,
                    "value_ids": [Command.create({"name": value}) for value in values],
                }
            )

        cls.variety = attribute("Soi", "soi", ["Gala", "Idared", "Golden"], 1)
        cls.grade = attribute("Calitate", "calitate", ["Extra", "Cat. I", "Cat. II"], 2)
        cls.size = attribute("Calibru", "calibru", ["65/70 mm", "70/75 mm", "75/80 mm"], 3)
        cls.color = attribute("Culoare", False, ["Roșu", "Galben"], 4)
        env.flush_all()

        cls.menu = env.ref("stock.menu_attribute_action", raise_if_not_found=False)

    def _list_url(self):
        url = "action=product.attribute_action&view_type=list"
        if self.menu:
            url += f"&menu_id={self.menu.id}"
        return url

    def _form_url(self, attribute):
        return f"id={attribute.id}&model=product.attribute&view_type=form"

    def test_capture_fise(self):
        # refuzul celui de-al doilea atribut cu același rol se loghează ca eroare SQL
        with mute_logger("odoo.sql_db", "odoo.http"):
            self.capture_screenshots(
                [
                    # 1. lista atributelor, cu coloana „Rol"
                    {
                        "url": self._list_url(),
                        "name": "01_lista_atribute_rol.png",
                        "wait": ".o_list_view",
                        "highlight": ["th[data-name='attribute_role']"],
                        "settle": 2000,
                    },
                    # 2. formularul atributului „Soi", cu câmpul „Rol"
                    {
                        "url": self._form_url(self.variety),
                        "name": "02_atribut_rol.png",
                        "wait": ".o_form_view",
                        "highlight": ["div[name='attribute_role']"],
                        "settle": 2000,
                    },
                    # 3. rolul „Soi" pe un al doilea atribut: baza refuză salvarea
                    {
                        "url": self._form_url(self.size),
                        "name": "03_rol_deja_folosit.png",
                        "wait": ".o_form_view",
                        "eval": TAKE_ROLE,
                        "eval_wait": 3500,
                        "highlight": [".modal .modal-content"],
                        "settle": 1500,
                    },
                ],
                hide_systray=True,
            )
