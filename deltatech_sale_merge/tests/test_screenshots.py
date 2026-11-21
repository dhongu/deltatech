# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Unirea ofertelor de vânzare", în RO (fișa) și EN (readme/USAGE.md),
# plus GIF-ul demo pentru pagina Apps.
#
# Seedează trei oferte ale clientului Agro Prod SRL (una cu alt agent de vânzări) și una a
# clientului Terra Construct SRL, pentru blocajul „client diferit".
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_sale_merge,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import json
import unittest
from datetime import timedelta

from odoo import Command, fields
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

# Pașii pe lista ofertelor, rulați în pagină: bifează ofertele după număr, deschide meniul
# Acțiuni și, în funcție de `stop`, merge mai departe până la wizard, la blocaj sau la unire.
ACTIONS_TOGGLE = ".o_cp_action_menus .dropdown-toggle:has([data-icon=settings])"

LIST_STEPS_JS = """(async (cfg) => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const facet = document.querySelector(".o_searchview .o_facet_remove");
    if (facet) {
        facet.click();
        await sleep(1200);
    }
    for (const name of cfg.names) {
        const row = [...document.querySelectorAll(".o_data_row")].find((r) => r.textContent.includes(name));
        row.querySelector(".o_list_record_selector input").click();
        await sleep(300);
    }
    document.querySelector(".o_cp_action_menus .dropdown-toggle:has([data-icon=settings])").click();
    await sleep(700);
    if (cfg.stop === "menu") {
        return;
    }
    [...document.querySelectorAll(".o-dropdown-item")]
        .find((e) => /Merge orders|Unește comenzile/.test(e.textContent))
        .click();
    await sleep(1500);
    if (cfg.sections) {
        document.querySelector(".modal div[name='add_sections'] input").click();
        await sleep(400);
    }
    if (cfg.stop === "wizard") {
        return;
    }
    document.querySelector(".modal button[name='action_merge']").click();
    await sleep(3000);
})(%s)"""

MERGE_ITEM = {
    "ro_RO": ".o-dropdown-item:has-text('Unește comenzile')",
    "en_US": ".o-dropdown-item:has-text('Merge orders')",
}


@tagged("-at_install", "post_install", "fise_screenshots")
class TestSaleMergeScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_sale_merge"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="RO Company")
        env = cls.env
        cls.salesperson = env["res.users"].create(
            {
                "name": "Maria Ionescu",
                "login": "maria.ionescu.merge",
                "group_ids": [Command.link(env.ref("sales_team.group_sale_salesman").id)],
            }
        )
        env.ref("base.user_admin").name = "Andrei Popescu"
        products = env["product.product"].create(
            [
                {"name": "Șurub M8 (cutie 100 buc)", "list_price": 25.0},
                {"name": "Piuliță M8 (cutie 100 buc)", "list_price": 18.0},
                {"name": "Șaibă M8 (cutie 100 buc)", "list_price": 9.5},
                {"name": "Diblu 8 mm (cutie 50 buc)", "list_price": 14.0},
            ]
        )
        surub, piulita, saiba, diblu = products
        # TVA 21% explicit și fără poziție fiscală: baza de capturi nu are planul de conturi RO,
        # iar poziția „Comerț exterior” din planul generic s-ar aplica automat clienților din RO
        tax_group = env["account.tax.group"].create({"name": "TVA 21%", "country_id": env.ref("base.ro").id})
        tax = env["account.tax"].create(
            {
                "name": "TVA 21%",
                "amount": 21.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "tax_group_id": tax_group.id,
            }
        )
        products.write({"taxes_id": [Command.set(tax.ids)]})
        agro = env["res.partner"].create({"name": "Agro Prod SRL", "country_id": env.ref("base.ro").id})
        terra = env["res.partner"].create({"name": "Terra Construct SRL", "country_id": env.ref("base.ro").id})
        admin = env.ref("base.user_admin")

        ron = env.company.currency_id
        pricelist = env["product.pricelist"].create({"name": "Listă de prețuri RON", "currency_id": ron.id})
        now = fields.Datetime.now()

        def order(partner, lines, days, user, ref=False):
            vals = {
                "partner_id": partner.id,
                "pricelist_id": pricelist.id,
                "fiscal_position_id": False,
                "user_id": user.id,
                "client_order_ref": ref,
                "date_order": now - timedelta(days=days),
                "order_line": [
                    Command.create({"product_id": p.id, "product_uom_qty": q, "tax_ids": [Command.set(tax.ids)]})
                    for p, q in lines
                ],
            }
            return env["sale.order"].create(vals)

        cls.order1 = order(agro, [(surub, 10), (piulita, 5)], 6, admin, ref="PO-1041")
        cls.order2 = order(agro, [(surub, 20), (saiba, 8)], 5, admin, ref="PO-1058")
        cls.order3 = order(agro, [(piulita, 5), (diblu, 12)], 4, cls.salesperson)
        cls.order4 = order(terra, [(surub, 3)], 3, admin)
        env.flush_all()

    def _list_url(self):
        action = self.env.ref("sale.action_quotations_with_onboarding").id
        return f"action={action}&view_type=list"

    def _steps(self, orders, stop, sections=False):
        cfg = {"names": orders.mapped("name"), "stop": stop, "sections": sections}
        return LIST_STEPS_JS % json.dumps(cfg)

    def _shots(self):
        three = self.order1 | self.order2 | self.order3
        return [
            {
                "url": self._list_url(),
                "name": "01_selectie_oferte.png",
                "wait": ".o_list_view .o_data_row",
                "eval": self._steps(three, "menu"),
                "eval_wait": 1500,
                "highlight": [MERGE_ITEM],
            },
            {
                "url": self._list_url(),
                "name": "02_wizard_unire.png",
                "wait": ".o_list_view .o_data_row",
                "eval": self._steps(three, "wizard", sections=True),
                "eval_wait": 2500,
                "highlight": [
                    ".modal div[name='target_mode']",
                    ".modal div[name='line_mode']",
                    ".modal div[name='add_sections']",
                ],
            },
            {
                "url": self._list_url(),
                "name": "03_blocaj_client_diferit.png",
                "wait": ".o_list_view .o_data_row",
                "eval": self._steps(self.order1 | self.order4, "merge"),
                "eval_wait": 4000,
                "settle": 2500,
            },
            {
                "url": self._list_url(),
                "name": "04_oferta_unita.png",
                "wait": ".o_list_view .o_data_row",
                "eval": self._steps(three, "merge", sections=True),
                "eval_wait": 5000,
                "full": True,
                "highlight": ["div[name='order_line'] tr.o_data_row:first-child", "tr.o_is_line_section"],
            },
            {
                "url": f"id={self.order1.id}&model=sale.order&view_type=form",
                "name": "05_date_pe_oferta_tinta.png",
                "wait": ".o_form_view",
                "click_tab": "Other Info",
                "eval": "0",
                "full": True,
                "highlight": ["div[name='merged_from_ids']", "div[name='client_order_ref']"],
            },
            {
                "url": f"id={self.order2.id}&model=sale.order&view_type=form",
                "name": "06_oferta_anulata.png",
                "wait": ".o_form_view",
                "click_tab": "Other Info",
                "eval": "0",
                "full": True,
                "hide_chatter": False,
                "highlight": ["div[name='merged_into_id']"],
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")

    def _gif_steps(self):
        three = self.order1 | self.order2 | self.order3
        action = self.env.ref("sale.action_quotations_with_onboarding").id
        menu = self.env.ref("sale.sale_menu_root").id
        names = three.mapped("name")
        steps = [{"goto": f"action={action}&menu_id={menu}&view_type=list", "wait": ".o_list_view .o_data_row"}]
        steps.append({"eval": 'document.querySelector(".o_searchview .o_facet_remove")?.click()', "hold": 1200})
        steps.append(
            {
                "caption": {
                    "ro_RO": "Trei oferte ale aceluiași client, pe care vrem să le unim",
                    "en_US": "Three quotations of the same customer, to be merged",
                }
            }
        )
        for name in names:
            steps.append({"click": f".o_data_row:has-text('{name}') .o_list_record_selector input", "hold": 300})
        steps += [
            {
                "caption": {
                    "ro_RO": "Din meniul Acțiuni se alege unirea",
                    "en_US": "The Actions menu offers the merge",
                },
                "click": ACTIONS_TOGGLE,
                "wait_after": ".o-dropdown-item",
            },
            {"click": MERGE_ITEM, "wait_after": ".modal .o_form_view", "hold": 600},
            {
                "caption": {
                    "ro_RO": "Se alege ținta și cum se tratează liniile",
                    "en_US": "The target and the lines are chosen",
                },
                "click": ".modal div[name='add_sections'] input",
                "hold": 1500,
            },
            {
                "caption": {
                    "ro_RO": "Ofertele unite se anulează, nu se șterg",
                    "en_US": "The merged quotations are cancelled, not deleted",
                },
                "click": ".modal button[name='action_merge']",
                "wait_after": ".o_form_view",
                "hold": 3500,
            },
            {"caption": "", "hide_cursor": True, "hold": 600},
        ]
        return steps

    def test_capture_gif(self):
        self.capture_gif(self._gif_steps())

    def test_capture_gif_en(self):
        self.capture_gif(self._gif_steps(), lang="en_US")
