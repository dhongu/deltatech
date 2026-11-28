# ©  2026 Deltatech
# See README.rst file on addons root folder for license details
#
# Screenshots for the consultant sheet (RO) and readme/USAGE.md (EN): the Cashiers Close the
# Register option next to Log in with Employees, the menu of an employee with basic rights with
# Close Register in it, the usual closing popup, and the menu of an employee with minimal rights,
# who still cannot close.
#
# Run:
#   ./odoo/odoo-bin -c odoo.conf -d <db> \
#       -i l10n_ro,deltatech_pos_cashier_close,deltatech_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import io
import unittest

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.deltatech_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    try:
        from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
    except ImportError:
        ScreenshotCase = None

JS_HELPERS = """
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    const wait = async (sel, timeout = 20000) => {
        const start = Date.now();
        while (Date.now() - start < timeout) {
            const el = document.querySelector(sel);
            if (el) { return el; }
            await sleep(100);
        }
        throw new Error('Not found: ' + sel);
    };
    const waitFor = async (fn, timeout = 40000) => {
        const start = Date.now();
        while (Date.now() - start < timeout) {
            const value = fn();
            if (value) { return value; }
            await sleep(100);
        }
        throw new Error('Timeout');
    };
"""

# Log the employee in (as the PIN screen would) and show the register.
LOGIN_AS = """
    const pos = await waitFor(() => window.posmodel && window.posmodel.models['hr.employee'] && window.posmodel);
    const employee = pos.models['hr.employee'].find((e) => e.name === EMPLOYEE);
    pos.setCashier(employee);
    const order = pos.getOrder() || pos.addNewOrder();
    pos.navigate('ProductScreen', {orderUuid: order.uuid});
    await wait('.product-screen', 40000);
    await sleep(1000);
"""

OPEN_MENU = """
    document.querySelector('.pos-topheader .fa-bars').closest('button').click();
    await wait('.pos-burger-menu-items');
    await sleep(600);
"""

CLOSE_REGISTER = """
    await pos.closeSession();
    await wait('.modal .payment-methods-overview, .modal .modal-body');
    await sleep(1200);
    // the cashier counted exactly the expected cash
    document.querySelector('.modal button.fa-clone').click();
    await sleep(600);
    document.activeElement?.blur();
    await sleep(300);
"""

CASHIER = "Ion Marin"
MINIMAL = "Elena Dobre"
MANAGER = "Ana Popescu"
DEVICE_LOGIN = "casa.centru"


def _picture(colour):
    from PIL import Image  # noqa: PLC0415

    buffer = io.BytesIO()
    Image.new("RGB", (400, 300), colour).save(buffer, format="PNG")
    return buffer.getvalue()


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPosCashierCloseScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_pos_cashier_close"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("deltatech_doc_screenshots indisponibil")
        super().setUpClass()
        cls.prepare_ro_company(name="Magazin Demo SRL")
        env = cls.env
        company = env.company
        admin = env.ref("base.user_admin")
        admin.write({"company_ids": [Command.link(company.id)], "company_id": company.id, "name": MANAGER})
        pos_manager = env.ref("point_of_sale.group_pos_manager")
        admin.group_ids = [Command.link(pos_manager.id)]
        env.user.sudo().group_ids = [Command.link(pos_manager.id)]

        # the login of the shop device: a plain POS user, as in a real shop. With the admin the
        # register would also show Cash In/Out to every cashier, a right of the Odoo user.
        cls.device_user = (
            env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Casa Magazin Centru",
                    "login": DEVICE_LOGIN,
                    "password": DEVICE_LOGIN,
                    "company_id": company.id,
                    "company_ids": [Command.set(company.ids)],
                    "group_ids": [
                        Command.set((env.ref("base.group_user") | env.ref("point_of_sale.group_pos_user")).ids)
                    ],
                    "lang": "ro_RO",
                }
            )
        )

        employees = (
            env["hr.employee"].sudo().create([{"name": name, "company_id": company.id} for name in (CASHIER, MINIMAL)])
        )
        cls.cashier, cls.minimal = employees
        manager = admin.employee_ids.filtered(lambda e: e.company_id == company)
        if not manager:
            manager = env["hr.employee"].sudo().create({"name": MANAGER, "company_id": company.id, "user_id": admin.id})

        tax = cls.company_data["default_tax_sale"]
        coffee = env["product.product"].create(
            {
                "name": "Cafea boabe 1 kg",
                "list_price": 74.30,
                "type": "consu",
                "available_in_pos": True,
                "company_id": company.id,
                "taxes_id": [Command.set(tax.ids)],
                "image_1920": _picture((111, 78, 55)),
            }
        )
        cash_journal = env["account.journal"].search(
            [*env["account.journal"]._check_company_domain(company), ("type", "=", "cash")], limit=1
        )
        cash = env["pos.payment.method"].create({"name": "Cash", "journal_id": cash_journal.id})
        cash.with_context(lang="ro_RO").name = "Numerar"
        cls.config = env["pos.config"].create(
            {
                "name": "Magazin Centru",
                "payment_method_ids": [Command.set(cash.ids)],
                "module_pos_hr": True,
                "advanced_employee_ids": [Command.set(manager.ids)],
                "basic_employee_ids": [Command.set(cls.cashier.ids)],
                "minimal_employee_ids": [Command.set(cls.minimal.ids)],
                "cashier_can_close": True,
            }
        )
        cls.config.open_ui()
        session = cls.config.current_session_id
        session.set_opening_control(0, "")
        cls._paid_order(session, coffee, cash)

    @classmethod
    def _paid_order(cls, session, product, method):
        """One coffee paid in cash, so the closing popup shows real amounts."""
        order = cls.env["pos.order"].create(
            {
                "session_id": session.id,
                "pos_reference": "26-0001-000001",
                "amount_total": 0,
                "amount_paid": 0,
                "amount_tax": 0,
                "amount_return": 0,
                "lines": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "qty": 1,
                            "price_unit": product.list_price,
                            "price_subtotal": product.list_price,
                            "price_subtotal_incl": 0,
                            "tax_ids": [Command.set(product.taxes_id.ids)],
                        }
                    )
                ],
            }
        )
        order.lines._onchange_amount_line_all()
        order._compute_prices()
        order.add_payment({"pos_order_id": order.id, "amount": order.amount_total, "payment_method_id": method.id})
        order._compute_prices()
        order.action_pos_order_paid()

    def _pos(self, name, employee, body, highlight=None):
        shot = {
            "path": f"/pos/ui/{self.config.id}",
            "name": name,
            "wait": ".pos",
            "timeout": 60000,
            "eval": "async () => {" + JS_HELPERS + LOGIN_AS.replace("EMPLOYEE", repr(employee)) + body + "}",
            "eval_wait": 500,
            "settle": 800,
        }
        if highlight:
            shot["highlight"] = highlight
        return shot

    def _shots(self):
        settings = self.env.ref("point_of_sale.action_pos_configuration").id
        pos_menu = self.env.ref("point_of_sale.menu_point_root").id
        close_item = {
            "ro_RO": ".pos-burger-menu-items .dropdown-item:has-text('Închide casa')",
            "en_US": ".pos-burger-menu-items .dropdown-item:has-text('Close Register')",
        }
        return [
            {
                "url": f"action={settings}&menu_id={pos_menu}&model=res.config.settings&view_type=form",
                "name": "01_setari_casierii_inchid_casa.png",
                "wait": ".o_form_view div[name='pos_cashier_can_close']",
                "timeout": 60000,
                "eval": "document.querySelector(\"div[name='pos_basic_employee_ids']\")"
                ".scrollIntoView({block: 'center'})",
                "highlight": [
                    "div[name='pos_basic_employee_ids']",
                    "div[name='pos_cashier_can_close']",
                ],
                "settle": 2500,
            },
            self._pos(
                "02_pos_meniu_casier.png",
                CASHIER,
                OPEN_MENU,
                highlight=[".pos-topheader .cashier-name", close_item],
            ),
            self._pos(
                "03_pos_inchidere_casa.png",
                CASHIER,
                CLOSE_REGISTER,
                highlight=[".modal button.fa-clone", ".modal .modal-footer .btn-primary"],
            ),
            self._pos("04_pos_meniu_drepturi_minime.png", MINIMAL, OPEN_MENU),
        ]

    def _capture(self, lang):
        # the settings with the admin, the register with the login of the shop device
        shots = self._shots()
        self.capture_screenshots(shots[:1], viewport=(1280, 720), hide_systray=True, lang=lang)
        self.capture_screenshots(shots[1:], login=DEVICE_LOGIN, viewport=(1280, 720), hide_systray=True, lang=lang)

    def test_capture_fise(self):
        self._capture("ro_RO")

    def test_capture_usage(self):
        self._capture("en_US")

    def _gif_steps(self):
        return [
            {
                "path": f"/pos/ui/{self.config.id}",
                "wait": ".pos",
                "timeout": 60000,
                "eval": "async () => {" + JS_HELPERS + LOGIN_AS.replace("EMPLOYEE", repr(CASHIER)) + "}",
            },
            {
                "caption": "A cashier with basic rights ends the shift",
                "move": ".pos-topheader .fa-bars",
                "hold": 1500,
            },
            {"click": ".pos-topheader button:has(.fa-bars)", "wait_after": ".pos-burger-menu-items"},
            {
                "caption": "Close Register is now in the menu",
                "move": ".pos-burger-menu-items .dropdown-item:has-text('Close Register')",
                "hold": 2000,
            },
            {
                "caption": "The usual closing popup opens",
                "click": ".pos-burger-menu-items .dropdown-item:has-text('Close Register')",
                "wait_after": ".modal .modal-footer",
                "hold": 2500,
            },
            {
                "caption": "Other manager rights stay with the managers",
                "move": ".modal .modal-footer .btn-primary",
                "hold": 2500,
            },
            {"caption": "", "hide_cursor": True, "hold": 600},
        ]

    def test_capture_gif(self):
        # deltatech has only the EN page on the Apps Store: static/description/en/demo.gif
        self.capture_gif(self._gif_steps(), login=DEVICE_LOGIN, lang="en_US")
