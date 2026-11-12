# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Capturi de ecran pentru fișa „Cod fiscal și e-mail unice la comanda online", în RO (fișa) și
# EN (readme/USAGE.md), pe compania „Demo Magazin SRL".
#
# Seed:
#   - clientul existent „Alfa Distribuție SRL", cod fiscal RO12345607, e-mail comenzi@alfa-distributie.example;
#   - clienta „Ioana Marin", utilizator de portal, cu un coș deschis pe site;
#   - firma „Beta Construct SRL", cod fiscal RO18547290, creată din adresa de facturare a clientului
#     „Mihai Pop", care a devenit contactul ei;
#   - setarea site-ului „Afișarea prețurilor produselor" = cu taxe, păstrată după o modificare a
#     adresei companiei (care recalculează setarea).
#
# Rulare:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_website_vat_validation,deltatech_doc_screenshots \
#       --test-tags=/deltatech_website_vat_validation:TestVatValidationScreenshots --stop-after-init
import json
import unittest

from odoo import Command
from odoo.tests import tagged

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

VIEWPORT = (1920, 1080)
# setările: doar rândul cu afișarea prețurilor și vecinii lui
SETTINGS_VIEWPORT = (1920, 370)
CUSTOMER_LOGIN = "ioana.marin"
EXISTING_VAT = "RO12345607"
# același cod, scris altfel: cu litere mici, spații și cu spații în jur
TYPED_VAT = " ro 12 34 56 07 "
EXISTING_EMAIL = "comenzi@alfa-distributie.example"
# codul fiscal (valid) al firmei create la comandă, la Pasul 5
NEW_VAT = "RO18547290"

# completează câmpurile formularului de adresă, apasă butonul de salvare și aduce mesajele în
# mijlocul ecranului; câmpurile se scriu direct, apoi formularul se trimite prin JS (RPC)
FILL_AND_SAVE_JS = """(async () => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    // interacțiunea formularului pornește după ce încarcă datele țării; fără ea, butonul trimite
    // formularul clasic și pagina devine răspunsul JSON
    await sleep(2000);
    const form = document.querySelector('form.address_autoformat');
    const values = %s;
    for (const [name, value] of Object.entries(values)) {
        form[name].value = value;
        form[name].dispatchEvent(new Event('change', {bubbles: true}));
    }
    // avertismentul standard „editați adresele de livrare și facturare" nu ține de pas
    document.querySelectorAll('.o_customer_address_fill > div > .alert-warning').forEach((el) => el.remove());
    // în coș butonul principal e „Confirmă" (unul pentru mobil, unul pentru desktop); în portal, „Salvează"
    const buttons = [...document.querySelectorAll('[name="website_sale_main_button"], #save_address')];
    buttons.find((button) => button.offsetParent !== null).click();
    for (let i = 0; i < 40 && !document.querySelector('#errors > *, #checkout_alerts > *'); i++) {
        await sleep(250);
    }
    await sleep(500);
    form.querySelector('input[name="%s"]').scrollIntoView({block: 'center'});
})()"""


def fill_and_save(values, focus):
    return FILL_AND_SAVE_JS % (json.dumps(values), focus)


@tagged("-at_install", "post_install", "fise_screenshots")
class TestVatValidationScreenshots(ScreenshotCase or object):
    screenshots_module = "deltatech_website_vat_validation"

    @classmethod
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        company = cls.prepare_ro_company(name="Demo Magazin SRL")
        env = cls.env
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id})
        country_ro = env.ref("base.ro")

        # site-ul în română (fără prefix în adresă) și în engleză (/en/...)
        cls.website = env["website"].search([("company_id", "=", company.id)], limit=1)
        langs = env["res.lang"].with_context(active_test=False).search([("code", "in", ("ro_RO", "en_US"))])
        langs.active = True
        ro = langs.filtered(lambda lang: lang.code == "ro_RO")
        cls.website.write({"language_ids": [Command.set(langs.ids)], "default_lang_id": ro.id})

        # clientul existent, al cărui cod fiscal și e-mail nu pot fi folosite de alt cont
        env["res.partner"].create(
            {
                "name": "Alfa Distribuție SRL",
                "is_company": True,
                "vat": EXISTING_VAT,
                "email": EXISTING_EMAIL,
                "phone": "+40 21 555 0100",
                "street": "Str. Fabricii nr. 5",
                "city": "Cluj-Napoca",
                "zip": "400001",
                "country_id": country_ro.id,
            }
        )

        # clienta care comandă online: utilizator de portal, cu un coș deschis pe site
        portal_user = (
            env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Ioana Marin",
                    "login": CUSTOMER_LOGIN,
                    "password": CUSTOMER_LOGIN,
                    "email": "ioana.marin@example.com",
                    "company_id": company.id,
                    "company_ids": [Command.set(company.ids)],
                    "group_ids": [Command.set([env.ref("base.group_portal").id])],
                }
            )
        )
        cls.customer = portal_user.partner_id
        cls.customer.write(
            {
                "phone": "+40 722 000 111",
                "street": "Str. Lalelelor nr. 12",
                "city": "București",
                "zip": "010203",
                "country_id": country_ro.id,
            }
        )
        # prețurile magazinului în lei, cu TVA 21%
        ron = env.ref("base.RON")
        ron.active = True
        env["product.pricelist"].search([]).currency_id = ron
        vat_21 = env["account.tax"].create(
            {"name": "TVA 21%", "amount": 21.0, "type_tax_use": "sale", "company_id": company.id}
        )
        product = env["product.product"].create(
            {
                "name": "Imprimantă laser A4",
                "list_price": 899.0,
                "is_published": True,
                "website_id": False,
                "taxes_id": [Command.set(vat_21.ids)],
            }
        )
        # moneda companiei de test poate rămâne alta decât leul: prețul în lei vine din lista de prețuri
        pricelists = env["product.pricelist"].search([])
        pricelists.item_ids.unlink()
        pricelists.write(
            {
                "item_ids": [
                    Command.create(
                        {
                            "applied_on": "0_product_variant",
                            "product_id": product.id,
                            "compute_price": "fixed",
                            "fixed_price": 899.0,
                        }
                    )
                ]
            }
        )
        env["sale.order"].create(
            {
                "partner_id": cls.customer.id,
                "website_id": cls.website.id,
                "company_id": company.id,
                "order_line": [Command.create({"product_id": product.id, "product_uom_qty": 1})],
            }
        )

        # setarea de afișare a prețurilor: cu taxe, apoi o modificare a adresei companiei, care o
        # recalculează (fără modul, Odoo o readuce la „fără taxe")
        cls.website.show_line_subtotals_tax_selection = "tax_included"
        env.flush_all()
        company.partner_id.street = "Str. Exemplu nr. 12"
        company.partner_id.flush_recordset()
        cls.website.invalidate_recordset()
        assert cls.website.show_line_subtotals_tax_selection == "tax_included"

        # Pasul 5 — firma creată din adresa de facturare a unei comenzi: persoana a completat
        # numele firmei și codul fiscal (nou), iar la salvare firma a fost creată, cu persoana contact
        buyer = env["res.partner"].create(
            {
                "name": "Mihai Pop",
                "email": "mihai.pop@beta-construct.example",
                "phone": "+40 744 123 456",
                "vat": NEW_VAT,
                "street": "Bd. Independenței nr. 7",
                "city": "Iași",
                "zip": "700001",
                "country_id": country_ro.id,
            }
        )
        # ce face Odoo la salvarea adresei de facturare cu „Firmă" completat
        buyer._create_parent_from_name("Beta Construct SRL")
        cls.created_company = buyer.parent_id

        cls.settings_action = env.ref("website.action_website_configuration")
        env.flush_all()

    def _customer_shots(self):
        billing = f"/shop/address?partner_id={self.customer.id}&address_type=billing"
        return [
            # Pasul 1 — codul fiscal al altui client, scris cu prefix, litere mici și spații
            {
                "path": {"ro_RO": billing, "en_US": f"/en{billing}"},
                "name": "01_cod_fiscal_duplicat_checkout.png",
                "wait": "form.address_autoformat",
                "eval": fill_and_save({"vat": TYPED_VAT}, "vat"),
                "eval_wait": 1500,
                # în checkout, Odoo 20 afișează mesajele în alerta din capul paginii (#checkout_alerts)
                "highlight": ["div:has(> input[name='vat'])", "#checkout_alerts"],
                "settle": 1500,
            },
            # Pasul 2 — adresa de e-mail a altui cont
            {
                "path": {"ro_RO": billing, "en_US": f"/en{billing}"},
                "name": "02_email_duplicat_checkout.png",
                "wait": "form.address_autoformat",
                "eval": fill_and_save({"email": EXISTING_EMAIL}, "email"),
                "eval_wait": 1500,
                "highlight": ["div:has(> input[name='email'])", "#checkout_alerts"],
                "settle": 1500,
            },
            # Pasul 3 — aceeași verificare în portal, la „Detaliile mele"
            {
                "path": {"ro_RO": "/my/account", "en_US": "/en/my/account"},
                "name": "03_cod_fiscal_duplicat_portal.png",
                "wait": "form.address_autoformat",
                "eval": fill_and_save({"vat": TYPED_VAT}, "vat"),
                "eval_wait": 1500,
                "highlight": ["div:has(> input[name='vat'])", "#errors"],
                "settle": 1500,
            },
        ]

    def _admin_shots(self):
        return [
            # Pasul 4 — setarea de afișare a prețurilor, păstrată după recalcul
            {
                "url": f"action={self.settings_action.id}",
                "name": "04_afisare_preturi_pastrata.png",
                "wait": "#website_tax_inclusion_setting",
                "timeout": 60000,
                # setarea sus, sub bara de control: în cadru nu mai intră blocul plăților de deasupra
                "eval": "document.querySelector('#website_tax_inclusion_setting').scrollIntoView({block: 'start'});"
                "document.querySelector('.settings').scrollBy(0, -12)",
                "highlight": ["#website_tax_inclusion_setting"],
                "settle": 2500,
            },
        ]

    def _company_shots(self):
        return [
            # Pasul 5 — firma creată la comandă: companie, cu adresa și codul fiscal tastate, iar
            # persoana care a comandat este contactul ei
            {
                "url": f"model=res.partner&id={self.created_company.id}&view_type=form",
                "name": "05_firma_creata_la_comanda.png",
                "wait": ".o_form_view .o_field_widget[name='child_ids']",
                "timeout": 60000,
                "highlight": [
                    ".o_field_widget[name='vat']",
                    ".o_field_widget[name='child_ids']",
                ],
                "settle": 2500,
            },
        ]

    def test_capture_fise(self):
        self.capture_screenshots(self._customer_shots(), login=CUSTOMER_LOGIN, viewport=VIEWPORT)
        self.capture_screenshots(self._admin_shots(), viewport=SETTINGS_VIEWPORT)
        self.capture_screenshots(self._company_shots(), viewport=VIEWPORT)

    def test_capture_usage(self):
        self.capture_screenshots(self._customer_shots(), login=CUSTOMER_LOGIN, viewport=VIEWPORT, lang="en_US")
        self.capture_screenshots(self._admin_shots(), viewport=SETTINGS_VIEWPORT, lang="en_US")
        self.capture_screenshots(self._company_shots(), viewport=VIEWPORT, lang="en_US")
