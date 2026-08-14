from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.test_frontend import TestPointOfSaleHttpCommon


@tagged("post_install", "-at_install")
class TestPosStockBadge(TestPointOfSaleHttpCommon):
    """The badge is built from an inherited owl template, so only a real POS session
    can prove that both the xpath and the price helper still match the core code."""

    def test_stock_badge_shows_price_and_quantity(self):
        self.main_pos_config.write({"display_stock": True, "display_price": True})
        self.main_pos_config.with_user(self.pos_user).open_ui()
        self.main_pos_config.current_session_id.set_opening_control(0, "")
        product = self.env["product.product"].create(
            {
                "name": "Stocked POS Product",
                "is_storable": True,
                "available_in_pos": True,
                "list_price": 100.0,
            }
        )
        self.env["stock.quant"]._update_available_quantity(product, self.main_pos_config.warehouse_id.lot_stock_id, 7)

        self.browser_js(
            self._get_url(),
            """
            (async () => {
                const waitFor = async (fn) => {
                    for (let i = 0; i < 100; i++) {
                        const value = fn();
                        if (value) {
                            return value;
                        }
                        await new Promise((r) => setTimeout(r, 200));
                    }
                    return null;
                };

                const openButton = await waitFor(() =>
                    [...document.querySelectorAll("button, .button")].find(
                        (el) => el.innerText.trim() === "Open Register"
                    )
                );
                if (!openButton) {
                    console.error("could not open the register");
                    return;
                }
                openButton.click();

                const badge = await waitFor(() => {
                    const pos = odoo.__WOWL_DEBUG__?.root?.env?.services?.pos;
                    const template = pos
                        ?.models["product.template"]
                        ?.getAll()
                        .find((t) => t.display_name === "Stocked POS Product");
                    if (!template) {
                        return null;
                    }
                    const card = document.querySelector(
                        `article[data-product-id="${template.id}"]`
                    );
                    return card?.querySelector(".product-stock-tag");
                });
                if (!badge) {
                    console.error("the stock badge was not rendered on the product card");
                    return;
                }
                if (!badge.querySelector(".product-price-badge")) {
                    console.error("the price is missing from the badge");
                    return;
                }
                const qty = badge.querySelector(".product-qty");
                if (!qty || qty.innerText.trim() !== "7") {
                    console.error("unexpected quantity in the badge: " + qty?.innerText);
                    return;
                }
                console.log("test successful");
            })();
            """,
            login="pos_user",
        )
