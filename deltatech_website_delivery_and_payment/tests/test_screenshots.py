# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Metode de livrare și de plată filtrate în checkout" —
# generate în timpul testelor: RO pentru fișa consultant, EN pentru readme/USAGE.md.
#
# Seed (date de exemplu, compania „Demo Magazin SRL", RON):
#   - furnizori de plată: Transfer bancar, Numerar la livrare (limită 1.500 lei, ascuns pentru
#     eticheta „Client restant") și Card la curier (furnizor manual pe metoda Card);
#   - metode de livrare: Curier rapid (permite Numerar la livrare și Card la curier),
#     Ridicare din depozit (permite doar Transfer bancar), Transport paletizat (de la 50 kg)
#     și Curier local București (ascuns pentru eticheta „Provincie");
#   - clientul „Maria Ionescu" (utilizator portal, din Cluj, eticheta „Provincie") cu un coș de
#     2 x „Set chei combinate 12 piese" (1,5 kg/buc.).
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_website_delivery_and_payment,deltatech_doc_screenshots \
#       --test-tags=/deltatech_website_delivery_and_payment:TestDeliveryPaymentScreenshots --stop-after-init
import unittest

from odoo import Command
from odoo.tests import tagged
from odoo.tools import BinaryBytes, file_open

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

VIEWPORT = (1920, 1080)
CUSTOMER_LOGIN = "maria.ionescu@example.com"
# tab-ul standard „Restrictions" (netradus în Odoo 20), unde modulul pune limita de valoare și etichetele
TAB_RESTRICTIONS = ".o_notebook_headers .nav-link:has-text('Restrictions')"
TAB_PAYMENT = {
    "ro_RO": ".o_notebook_headers .nav-link:has-text('Plată')",
    "en_US": ".o_notebook_headers .nav-link:has-text('Payment Acquirer')",
}


@tagged("-at_install", "post_install", "fise_screenshots")
class TestDeliveryPaymentScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_website_delivery_and_payment"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        company = cls.prepare_ro_company(name="Demo Magazin SRL")
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        ron = company.currency_id

        # site-ul în română, ca limbă implicită; EN rămâne disponibilă pentru capturile USAGE
        cls.website = env["website"].search([("company_id", "=", company.id)], limit=1)
        ro = env["res.lang"].search([("code", "=", "ro_RO")], limit=1)
        en = env.ref("base.lang_en")
        cls.website.write({"language_ids": [Command.link(ro.id), Command.link(en.id)], "default_lang_id": ro.id})
        env["product.pricelist"].search([]).write({"currency_id": ron.id})

        # TVA 21% pe produse și pe livrare, ca în orice magazin B2C din RO
        cls.tax = env["account.tax"].create(
            {"name": "TVA 21%", "amount": 21.0, "type_tax_use": "sale", "company_id": company.id}
        )

        # etichete de client
        Tag = env["res.partner.category"]
        cls.tag_provincie = Tag.create({"name": "Provincie", "color": 4})
        cls.tag_restant = Tag.create({"name": "Client restant", "color": 1})

        # furnizori de plată: toți furnizori manuali, fără date reale de cont
        cls.wire = env.ref("payment.payment_provider_transfer")
        cls.wire.write({"name": "Transfer bancar", "is_live": True, "active": True, "is_published": True})
        cls.cod = env.ref("delivery.payment_provider_cod")
        cls.cod.write(
            {
                "name": "Numerar la livrare",
                "is_live": True,
                "active": True,
                "is_published": True,
                "value_limit": 1500.0,
                "restrict_label_ids": [Command.set(cls.tag_restant.ids)],
            }
        )
        cls.card = env["payment.provider"].create(
            {
                "name": "Card la curier",
                "code": "custom",
                "custom_mode": "wire_transfer",
                "is_live": True,
                "active": True,
                "is_published": True,
            }
        )
        # în Odoo 20 o metodă de plată aparține unui singur furnizor: „Card" se creează pe Card la curier
        env["payment.method"].create(
            {
                "name": "Card",
                "code": "card",
                "provider_id": cls.card.id,
                "active": True,
                "image": BinaryBytes(file_open("payment/static/img/card.png", "rb").read()),
            }
        )
        cls.card.with_context(active_test=False).payment_method_ids.filtered(lambda m: m.code != "card").write(
            {"active": False}
        )
        (env["payment.provider"].search([]) - cls.wire - cls.cod - cls.card).write({"is_published": False})
        for provider in cls.wire | cls.cod | cls.card:
            provider.payment_method_ids.write({"active": True})

        # metode de livrare
        env["delivery.carrier"].search([]).write({"is_published": False})

        def carrier(name, price, **vals):
            # câte un produs de livrare pe metodă: prețul fix stă pe produs
            product = env["product.product"].create(
                {"name": name, "type": "service", "list_price": price, "taxes_id": [Command.set(cls.tax.ids)]}
            )
            return env["delivery.carrier"].create(
                {
                    "name": name,
                    "delivery_type": "fixed",
                    "fixed_price": price,
                    "product_id": product.id,
                    "is_published": True,
                    "website_id": False,
                    **vals,
                }
            )

        cls.carrier_courier = carrier(
            "Curier rapid",
            25.0,
            allow_cash_on_delivery=True,
            acquirer_allowed_ids=[Command.set((cls.cod | cls.card).ids)],
        )
        cls.carrier_pickup = carrier("Ridicare din depozit", 0.0, acquirer_allowed_ids=[Command.set(cls.wire.ids)])
        cls.carrier_pallet = carrier("Transport paletizat", 180.0, weight_min=50.0)
        cls.carrier_local = carrier(
            "Curier local București", 15.0, restrict_label_ids=[Command.set(cls.tag_provincie.ids)]
        )

        # clientul, utilizator portal (parola = login, cum cere capture_screenshots)
        state_cj = env["res.country.state"].search(
            [("country_id", "=", env.ref("base.ro").id), ("code", "=", "CJ")], limit=1
        )
        cls.customer_user = (
            env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Maria Ionescu",
                    "login": CUSTOMER_LOGIN,
                    "password": CUSTOMER_LOGIN,
                    "email": CUSTOMER_LOGIN,
                    "company_id": company.id,
                    "company_ids": [Command.set(company.ids)],
                    "group_ids": [Command.set(env.ref("base.group_portal").ids)],
                }
            )
        )
        cls.customer = cls.customer_user.partner_id
        cls.customer.write(
            {
                "street": "Str. Memorandumului nr. 1",
                "city": "Cluj-Napoca",
                "zip": "400114",
                "state_id": state_cj.id,
                "country_id": env.ref("base.ro").id,
                "phone": "+40 700 000 000",
                "category_id": [Command.set(cls.tag_provincie.ids)],
                "company_id": company.id,
            }
        )

        # coșul: 2 x 1,5 kg = 3 kg, sub pragul de 50 kg al transportului paletizat
        cls.product = env["product.product"].create(
            {
                "name": "Set chei combinate 12 piese",
                "type": "consu",
                "list_price": 189.0,
                "weight": 1.5,
                "is_published": True,
                "website_id": False,
                "taxes_id": [Command.set(cls.tax.ids)],
            }
        )
        cls.order = env["sale.order"].create(
            {
                "partner_id": cls.customer.id,
                "website_id": cls.website.id,
                "company_id": company.id,
                "order_line": [Command.create({"product_id": cls.product.id, "product_uom_qty": 2})],
            }
        )
        cls.order._set_delivery_method(cls.carrier_courier)

        cls.carrier_action = env.ref("delivery.action_delivery_carrier_form")
        cls.provider_action = env.ref("payment.action_payment_provider")
        cls.partner_action = env.ref("base.action_partner_customer_form")
        cls.website_menu = env.ref("website.menu_website_configuration")
        env.flush_all()

    # -- shot-uri -------------------------------------------------------------------------

    def _carrier_shot(self, carrier, name, highlight, tab=None):
        shot = {
            "url": f"action={self.carrier_action.id}&menu_id={self.website_menu.id}&id={carrier.id}"
            "&model=delivery.carrier&view_type=form",
            "name": name,
            "wait": ".o_form_view",
            "highlight": highlight,
            "settle": 2000,
        }
        if tab:
            shot.update({"click_btn": TAB_PAYMENT, "wait_after": "div[name='acquirer_allowed_ids']"})
        return shot

    def _backend_shots(self):
        return [
            # Pasul 1 — furnizorii de plată permiși cu metoda de livrare
            self._carrier_shot(
                self.carrier_courier,
                "01_livrare_furnizori_permisi.png",
                [TAB_PAYMENT, "div[name='acquirer_allowed_ids']"],
                tab=True,
            ),
            # Pasul 2 — limitele de greutate
            self._carrier_shot(
                self.carrier_pallet,
                "02_livrare_limite_greutate.png",
                ["div.o_row:has(div[name='weight_min'])"],
            ),
            # Pasul 3 — metoda de livrare ascunsă pentru o etichetă de client
            self._carrier_shot(
                self.carrier_local,
                "03_livrare_restrictie_eticheta.png",
                [TAB_PAYMENT, "div[name='restrict_label_ids']"],
                tab=True,
            ),
            # Pasul 4 — furnizorul de plată: limita de valoare și etichetele
            {
                "url": f"action={self.provider_action.id}&menu_id={self.website_menu.id}&id={self.cod.id}"
                "&model=payment.provider&view_type=form",
                "name": "04_furnizor_plata_restrictii.png",
                "wait": ".o_form_view",
                "click_btn": TAB_RESTRICTIONS,
                "wait_after": "div[name='value_limit']",
                "eval": "document.querySelector(\"div[name='value_limit']\").scrollIntoView({block: 'center'})",
                "highlight": ["div[name='value_limit']", "div[name='restrict_label_ids']"],
                "settle": 2000,
            },
            # Pasul 5 — etichetele clientului
            {
                "url": f"action={self.partner_action.id}&menu_id={self.website_menu.id}&id={self.customer.id}"
                "&model=res.partner&view_type=form",
                "name": "05_client_etichete.png",
                "wait": ".o_form_view",
                "highlight": ["div[name='category_id']"],
                "settle": 2000,
            },
        ]

    def _checkout_shot(self, name, highlight):
        # site-ul are româna ca limbă implicită; engleza se servește cu prefixul /en
        page = "/shop/checkout" if name.startswith("06") else "/shop/payment"
        return {
            "path": {"ro_RO": page, "en_US": f"/en{page}"},
            "name": name,
            "wait": "#o_delivery_methods" if name.startswith("06") else "#o_payment_form_options",
            "eval": f"document.querySelector('{highlight}').scrollIntoView({{block: 'center'}})",
            "highlight": highlight,
            "settle": 2500,
        }

    def _capture(self, lang):
        self.customer.lang = lang
        self.order._set_delivery_method(self.carrier_courier)
        self.order.order_line.product_uom_qty = 2
        self.env.flush_all()
        self.capture_screenshots(self._backend_shots(), viewport=VIEWPORT, lang=lang)
        # Pasul 6 — pasul de livrare: lipsesc Transport paletizat și Curier local București
        # Pasul 7 — pasul de plată cu Curier rapid: Numerar la livrare și Card la curier
        self.capture_screenshots(
            [
                self._checkout_shot("06_site_pas_livrare.png", "#o_delivery_methods"),
                self._checkout_shot("07_site_plata_curier.png", "#o_payment_form_options ul.list-group"),
            ],
            login=CUSTOMER_LOGIN,
            viewport=VIEWPORT,
            lang=lang,
        )
        # Pasul 8 — cu Ridicare din depozit rămâne doar Transfer bancar
        self.order._set_delivery_method(self.carrier_pickup)
        self.env.flush_all()
        self.capture_screenshots(
            [self._checkout_shot("08_site_plata_ridicare.png", "#o_payment_form_options ul.list-group")],
            login=CUSTOMER_LOGIN,
            viewport=VIEWPORT,
            lang=lang,
        )
        # Pasul 9 — peste limita de 1.500 lei dispare Numerar la livrare
        self.order._set_delivery_method(self.carrier_courier)
        self.order.order_line.product_uom_qty = 10
        self.env.flush_all()
        self.capture_screenshots(
            [self._checkout_shot("09_site_plata_peste_limita.png", "#o_payment_form_options ul.list-group")],
            login=CUSTOMER_LOGIN,
            viewport=VIEWPORT,
            lang=lang,
        )

    def test_capture_fise(self):
        self._capture("ro_RO")

    def test_capture_usage(self):
        self._capture("en_US")
