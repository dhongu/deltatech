# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Coduri UNECE pe unitățile de măsură" — generate în timpul
# testelor, în limba RO (fișa) și EN (readme/USAGE.md).
#
# Fluxul: setarea care deschide lista unităților, nomenclatorul de coduri UNECE (filtrat pe
# ambalaje), lista unităților cu coloana Cod UNECE, o unitate proprie „Cutie 13 kg" cu codul
# XBX și factura emisă în această unitate. XML-ul UBL al facturii se generează în test și se
# loghează ca extras pentru fișă.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_uom_unece,deltatech_doc_screenshots \
#       --test-tags=/deltatech_uom_unece:TestUomUneceScreenshots --stop-after-init
import json
import logging
import unittest

from lxml import etree

from odoo import Command, fields
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

_logger = logging.getLogger(__name__)

# afișează coloanele opționale ale unei liste, ca operatorul din meniul de coloane (⇄) al listei
SHOW_OPTIONAL_COLUMNS_JS = """async () => {{
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const scope = document.querySelector("{scope}");
    for (const name of {names}) {{
        if (scope.querySelector(`th[data-name='${{name}}']`)) {{
            continue;
        }}
        scope.querySelector(".o_optional_columns_dropdown_toggle").click();
        await sleep(500);
        document.querySelector(`.o-dropdown--menu input[name='${{name}}']`).click();
        await sleep(800);
        document.body.click();
        await sleep(300);
    }}
}}"""


def _show_columns(names, scope=".o_list_view"):
    return SHOW_OPTIONAL_COLUMNS_JS.format(scope=scope, names=json.dumps(names))


# în Setări, blocul „Unități și ambalaje" din secțiunea Facturare
SCROLL_TO_UOM_SETTING_JS = """async () => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    for (let i = 0; i < 50 && !document.querySelector("#account_uom"); i++) {
        await sleep(100);
    }
    const setting = document.querySelector("#account_uom");
    setting.scrollIntoView({block: "start"});
    // titlul blocului „Unități și ambalaje" rămâne vizibil deasupra setării
    let box = setting.parentElement;
    while (box && box.scrollHeight <= box.clientHeight) {
        box = box.parentElement;
    }
    if (box) {
        box.scrollTop -= 70;
    }
}"""


@tagged("-at_install", "post_install", "fise_screenshots")
class TestUomUneceScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_uom_unece"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company()
        env = cls.env
        admin = env.ref("base.user_admin")
        # „Unități de măsură și ambalaje" bifat în Setări: lista unităților și coloana UM pe factură
        env.ref("base.group_user").implied_ids = [Command.link(env.ref("uom.group_uom").id)]
        admin.group_ids = [Command.link(env.ref("uom.group_uom").id)]
        # nomenclatorul se deschide direct pe ambalaje (Rec 21), unde e codul folosit mai jos
        cls.code_action = env.ref("deltatech_uom_unece.uom_unece_code_action")
        cls.code_action.context = "{'search_default_packaging': 1}"
        cls.uom_action = env.ref("uom.uom_uom_action_list")

        kg = env.ref("uom.product_uom_kgm")
        cls.box = env["uom.uom"].create(
            {
                "name": "Cutie 13 kg",
                "relative_uom_id": kg.id,
                "relative_factor": 13,
                "unece_code_id": env.ref("deltatech_uom_unece.unece_xbx").id,
            }
        )
        cls.box.update_field_translations("name", {"ro_RO": "Cutie 13 kg", "en_US": "Box of 13 kg"})

        cls.product = env["product.product"].create(
            {
                "name": "Detergent pudră profesional",
                "default_code": "DET-13",
                "type": "consu",
                "uom_id": cls.box.id,
                "list_price": 245.0,
            }
        )
        cls.product.product_tmpl_id.update_field_translations(
            "name", {"ro_RO": "Detergent pudră profesional", "en_US": "Professional laundry powder"}
        )
        partner = env["res.partner"].create(
            {
                "name": "Client Demo SRL",
                "vat": "RO18547290",
                "street": "Str. Clientului nr. 5",
                "city": "Cluj-Napoca",
                "zip": "400001",
                "country_id": env.ref("base.ro").id,
                "lang": "ro_RO",
            }
        )
        tax = env.company.account_sale_tax_id
        cls.invoice = env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "fiscal_position_id": False,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "quantity": 10,
                            "product_uom_id": cls.box.id,
                            "price_unit": 245.0,
                            "tax_ids": [Command.set(tax.ids)],
                        }
                    )
                ],
            }
        )
        cls.invoice.action_post()

    def _log_xml_excerpt(self):
        """Extrasul UBL pentru fișă: unitCode-ul liniei vine din codul pus pe unitate."""
        xml, _errors = self.env["account.edi.xml.ubl_bis3"]._export_invoice(self.invoice)
        self.assertIn(b'unitCode="XBX"', xml)
        tree = etree.fromstring(xml)
        line = tree.find("{*}InvoiceLine")
        excerpt = self.xml_excerpt(etree.tostring(line), max_lines=40)
        _logger.info("Extras UBL pentru fișă:\n%s", excerpt)

    def _shots(self):
        return [
            # 1. Setări → Facturare → Unități și ambalaje: activarea și drumul spre lista unităților
            {
                "url": "action=account.action_account_config",
                "name": "01_setare_unitati_ambalaje.png",
                "wait": "#account_uom",
                "eval": SCROLL_TO_UOM_SETTING_JS,
                "eval_wait": 1500,
                "highlight": ["#account_uom .o-checkbox", "#account_uom button.btn-link"],
            },
            # 2. Setări → Coduri UNECE, filtrat pe ambalaje (Rec 21)
            {
                "url": f"action={self.code_action.id}&view_type=list",
                "name": "02_coduri_unece_ambalaje.png",
                "wait": ".o_list_view .o_data_row",
                "highlight": [
                    "nav.o_main_navbar a.dropdown-item[data-menu-xmlid='deltatech_uom_unece.uom_unece_code_menu'],"
                    " nav.o_main_navbar [data-menu-xmlid='deltatech_uom_unece.uom_unece_code_menu']",
                    ".o_searchview_facet",
                ],
            },
            # 3. lista unităților, cu coloana opțională Cod UNECE afișată
            {
                "url": f"action={self.uom_action.id}&view_type=list",
                "name": "03_unitati_coloana_cod_unece.png",
                "wait": ".o_list_view .o_data_row",
                "eval": _show_columns(["unece_code_id"]),
                "eval_wait": 1500,
                "highlight": {
                    "ro_RO": [".o_data_row:has-text('Cutie 13 kg') td[name='unece_code_id']"],
                    "en_US": [".o_data_row:has-text('Box of 13 kg') td[name='unece_code_id']"],
                },
            },
            # 4. unitatea proprie „Cutie 13 kg", cu codul XBX
            {
                "url": f"action={self.uom_action.id}&id={self.box.id}&model=uom.uom&view_type=form",
                "name": "04_unitate_cutie_cod_unece.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='unece_code_id']"],
            },
            # 5. factura emisă în această unitate
            {
                "url": (
                    f"menu_id={self.env.ref('account.menu_finance').id}"
                    f"&action=account.action_move_out_invoice_type"
                    f"&id={self.invoice.id}&model=account.move&view_type=form"
                ),
                "name": "05_factura_unitate_cutie.png",
                "wait": ".o_form_view",
                "click_tab": {"ro_RO": "Linii factură", "en_US": "Invoice Lines"},
                # fără aplicația Vânzări, Cantitate și UM sunt ascunse implicit pe liniile facturii
                "eval": _show_columns(["quantity", "product_uom_id"], scope="div[name='invoice_line_ids']"),
                "eval_wait": 1500,
                "highlight": ["td[name='product_uom_id']"],
            },
        ]

    def test_capture_fise(self):
        self._log_xml_excerpt()
        self.capture_screenshots(self._shots(), viewport=(1600, 900), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), viewport=(1600, 900), lang="en_US", hide_systray=True)
