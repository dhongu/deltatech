# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Detalii de configurație pe liniile comenzii de vânzare” —
# generate în timpul testelor, pe compania „Demo Tâmplărie SRL” în RON: în RO pentru fișă și în
# EN (static/description/en/) pentru readme/USAGE.md, plus GIF-ul demo pentru Apps Store.
#
# Seedează o comandă de vânzare cu trei linii, așa cum ar crea-o un conector de configurator:
# o fereastră PVC și o ușă de balcon cu detaliile de configurație (identitate și poziție,
# dimensiuni L×H, profil, culoare, părți, schița produsului ca imagine) și o linie de montaj
# fără detalii.
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i deltatech_sale_linie_config_details,l10n_ro,deltatech_doc_screenshots \
#       --test-tags=/deltatech_sale_linie_config_details:TestConfigDetailsScreenshots --stop-after-init
import io
import unittest

from odoo import Command
from odoo.tests import tagged
from odoo.tools import BinaryBytes

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

DETAILS_BUTTON = "tr.o_data_row:nth-child(%d) button[name='action_open_config_details']"


def window_picture(panes, frame=(236, 236, 236), glass=(173, 216, 230)):
    """Schița unei tâmplării PVC (PNG), ca imagine de produs: ``panes`` canate alăturate."""
    from PIL import Image, ImageDraw  # noqa: PLC0415 - doar la seed

    width, height = 120 * panes + 40, 300
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, width - 10, height - 10], fill=frame, outline=(90, 90, 90), width=4)
    for i in range(panes):
        x0 = 20 + i * 120
        draw.rectangle([x0, 20, x0 + 110, height - 20], fill=glass, outline=(90, 90, 90), width=3)
        draw.line([x0 + 95, height // 2 - 20, x0 + 95, height // 2 + 20], fill=(60, 60, 60), width=5)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return BinaryBytes(buf.getvalue())


@tagged("-at_install", "post_install", "fise_screenshots")
class TestConfigDetailsScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_sale_linie_config_details"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Demo Tâmplărie SRL")
        company = cls.env.company
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        for xmlid in ("sales_team.group_sale_salesman",):
            group = env.ref(xmlid)
            env.user.group_ids = [Command.link(group.id)]
            admin.group_ids = [Command.link(group.id)]
        env["product.pricelist"].search([]).write({"name": "Listă de prețuri RON"})
        env.flush_all()

        ro = env.ref("base.ro").id
        cls.customer = env["res.partner"].create({"name": "Casa Verde Residence SRL", "country_id": ro})
        cls.window = env["product.product"].create(
            {"name": "Fereastră PVC 2 canate", "list_price": 1850.0, "image_1920": window_picture(2)}
        )
        cls.door = env["product.product"].create(
            {"name": "Ușă balcon PVC", "list_price": 2650.0, "image_1920": window_picture(1)}
        )
        cls.mounting = env["product.product"].create(
            {"name": "Montaj tâmplărie", "type": "service", "list_price": 350.0}
        )

        window_details = [
            {"name": "Identitate", "value": {"id": "WX-10452", "Poziție": "P1", "Încăpere": "Dormitor"}},
            {"name": "Dimensiuni", "value": {"L (mm)": 1200, "H (mm)": 1400}},
            {"name": "Profil", "value": {"Sistem": "Salamander BluEvolution 82", "Camere": 6}},
            {"name": "Culoare", "value": {"Exterior": "Antracit RAL 7016", "Interior": "Alb"}},
            {
                "name": "Părți",
                "value": {
                    "Ușă stânga": {"x": 600, "y": 1400, "Deschidere": "oscilobatantă"},
                    "Ușă dreapta": {"x": 600, "y": 1400, "Deschidere": "fixă"},
                },
            },
            {"name": "Schiță", "value": {"image": f"/web/image/product.product/{cls.window.id}/image_256"}},
            {"name": "Observații", "value": "Glaf interior inclus"},
        ]
        door_details = [
            {"name": "Identitate", "value": {"id": "WX-10453", "Poziție": "P2", "Încăpere": "Living"}},
            {"name": "Dimensiuni", "value": {"L (mm)": 900, "H (mm)": 2200}},
            {"name": "Profil", "value": {"Sistem": "Salamander BluEvolution 82", "Camere": 6}},
            {"name": "Culoare", "value": {"Exterior": "Antracit RAL 7016", "Interior": "Alb"}},
            {"name": "Părți", "value": {"Ușă": {"x": 900, "y": 2200, "Deschidere": "batantă"}}},
            {
                "name": "Machetă",
                "value": {
                    "image": f"/web/image/product.product/{cls.door.id}/image_256",
                    "src": f"/web/image/product.product/{cls.door.id}/image_512",
                },
            },
        ]
        cls.order = env["sale.order"].create(
            {
                "partner_id": cls.customer.id,
                "client_order_ref": "Configurator WX-10452",
                "order_line": [
                    Command.create(
                        {"product_id": cls.window.id, "product_uom_qty": 4.0, "config_details": window_details}
                    ),
                    Command.create({"product_id": cls.door.id, "product_uom_qty": 1.0, "config_details": door_details}),
                    Command.create({"product_id": cls.mounting.id, "product_uom_qty": 5.0}),
                ],
            }
        )

    def _order_url(self):
        action = self.env.ref("sale.action_quotations_with_onboarding")
        menu = self.env.ref("sale.sale_menu_root")
        return f"action={action.id}&menu_id={menu.id}&id={self.order.id}&model=sale.order&view_type=form"

    def _shots(self):
        order = self._order_url()
        return [
            # 1. comanda: coloana cu butonul Detalii, doar pe liniile care au configurație (CA7, CA4)
            {
                "url": order,
                "name": "01_comanda_buton_detalii.png",
                "wait": ".o_form_view .o_data_row",
                "highlight": [DETAILS_BUTTON % 1, DETAILS_BUTTON % 2],
                "settle": 2000,
            },
            # 2. fereastra de detalii a ferestrei PVC: grupuri, valori, părți imbricate, schița (CA2, CA6)
            {
                "url": order,
                "name": "02_popup_detalii_fereastra.png",
                "wait": ".o_form_view .o_data_row",
                "click_btn": DETAILS_BUTTON % 1,
                "wait_after": ".modal .o_form_view",
                "highlight": [".modal strong"],
                "settle": 2000,
            },
            # 3. fereastra de detalii a ușii de balcon: imaginile și linkul de deschidere (CA5)
            {
                "url": order,
                "name": "03_popup_detalii_imagini.png",
                "wait": ".o_form_view .o_data_row",
                "click_btn": DETAILS_BUTTON % 2,
                "wait_after": ".modal .o_form_view",
                "highlight": [".modal .o_field_html img", ".modal .o_field_html a[target='_blank']"],
                "settle": 2500,
            },
        ]

    def _gif_steps(self):
        return [
            {"goto": self._order_url(), "wait": ".o_form_view .o_data_row"},
            {
                "caption": {
                    "ro_RO": "Comanda vine de la configurator, cu tot ce s-a ales",
                    "en_US": "The order comes from the configurator, fully specified",
                },
                "move": DETAILS_BUTTON % 1,
                "hold": 2500,
            },
            {
                "caption": {
                    "ro_RO": "Butonul Detalii apare doar pe liniile configurate",
                    "en_US": "The Details button shows only on configured lines",
                },
                "move": "tr.o_data_row:nth-child(3)",
                "hold": 2200,
            },
            {
                "caption": {
                    "ro_RO": "Un clic deschide configurația ferestrei",
                    "en_US": "One click opens the window configuration",
                },
                "click": DETAILS_BUTTON % 1,
                "wait_after": ".modal .o_form_view",
                "hold": 3500,
            },
            {
                "caption": {
                    "ro_RO": "Dimensiuni, profil, culoare și părți, fără a părăsi comanda",
                    "en_US": "Dimensions, profile, colour and parts, right on the order",
                },
                "move": ".modal .modal-title",
                "hold": 3000,
            },
            {"caption": "", "hide_cursor": True, "hold": 600},
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._shots(), hide_systray=True)

    def test_capture_usage(self):
        self.capture_screenshots(self._shots(), hide_systray=True, lang="en_US")

    def test_capture_gif(self):
        # suita deltatech are doar pagina EN pe Apps Store: GIF-ul RO nu se folosește
        self.capture_gif(self._gif_steps(), lang="en_US")
