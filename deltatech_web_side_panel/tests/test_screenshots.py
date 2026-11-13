# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Panou lateral cu detaliile înregistrării”, în RO (fișa) și EN
# (readme/USAGE.md). Panoul apare doar la ferestre de cel puțin 1200 px: viewport-ul implicit
# al ScreenshotCase (1920 px) e suficient.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_web_side_panel,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import json
import unittest

from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

PANEL = ".o_side_panel"
# numele contactului pe care se dă click, în kanban și în listă
SELECTED = "Agro Prod SRL"

# Pașii unui ecran, rulați în pagină, cu pauză între ei ca să se randeze panoul.
STEPS_JS = """(async () => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const steps = %s;
    for (const [kind, arg, value] of steps) {
        if (kind === "select") {
            const rows = [...document.querySelectorAll(".o_kanban_record, .o_data_row")];
            const row = rows.find((r) => r.textContent.includes(arg));
            (row.querySelector("td[name='complete_name'], .fw-bold") || row).click();
        } else if (kind === "key") {
            const handle = document.querySelector(".o_side_panel_resizer");
            handle.focus();
            for (let i = 0; i < value; i++) {
                handle.dispatchEvent(new KeyboardEvent("keydown", {key: arg, shiftKey: true, bubbles: true}));
                await sleep(60);
            }
        }
        await sleep(1000);
    }
})()"""


def steps(*items):
    return STEPS_JS % json.dumps([list(item) + [None] * (3 - len(item)) for item in items])


@tagged("-at_install", "post_install", "fise_screenshots")
class TestSidePanelScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_web_side_panel"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        env = cls.env
        partner = env["res.partner"]
        # fără alți contacți în ecran: capturile arată doar datele seedate
        partner.search([("id", "not in", [env.ref("base.partner_root").id])]).filtered(
            lambda p: not p.user_ids and p != env.company.partner_id
        ).write({"active": False})
        cls.company_partner = partner.create(
            {
                "name": SELECTED,
                "is_company": True,
                "email": "contact@agroprod.example.ro",
                "phone": "+40 244 555 100",
                "street": "Str. Morii nr. 5",
                "zip": "100001",
                "city": "Ploiești",
                "country_id": env.ref("base.ro").id,
                "comment": "Client din 2021, plătește la 30 de zile.",
            }
        )
        for name, city in (
            ("Delta Transport SRL", "Brașov"),
            ("Ferma Verde SRL", "Cluj-Napoca"),
            ("Popescu Ion PFA", "Iași"),
            ("Tehnic Service SRL", "Timișoara"),
        ):
            partner.create(
                {
                    "name": name,
                    "is_company": True,
                    "email": f"office@{name.split()[0].lower()}.example.ro",
                    "phone": "+40 722 000 111",
                    "city": city,
                    "country_id": env.ref("base.ro").id,
                }
            )
        action = env.ref("deltatech_web_side_panel.action_demo_partners").id
        cls.action = action

    def _url(self, view_type):
        return f"action={self.action}&model=res.partner&view_type={view_type}"

    def _shots(self):
        return [
            {
                "url": self._url("kanban"),
                "name": "01_kanban_cu_panou.png",
                "wait": ".o_kanban_record",
                "eval": steps(("select", SELECTED)),
                "highlight": [".o_side_panel_selected", ".o_side_panel_body"],
            },
            {
                "url": self._url("list"),
                "name": "02_lista_cu_panou.png",
                "wait": ".o_data_row",
                "eval": steps(("select", SELECTED)),
                "highlight": [".o_side_panel_selected", ".o_side_panel_prev", ".o_side_panel_open"],
            },
            {
                "url": self._url("kanban"),
                "name": "03_redimensionare_panou.png",
                "wait": ".o_kanban_record",
                "eval": steps(("select", SELECTED), ("key", "ArrowLeft", 8)),
                "highlight": [".o_side_panel_resizer"],
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots())

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), lang="en_US")
