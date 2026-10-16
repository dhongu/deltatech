import {describe, expect, test} from "@odoo/hoot";
import {animationFrame, click} from "@odoo/hoot-dom";
import {mountWithCleanup, onRpc, patchWithCleanup} from "@web/../tests/web_test_helpers";
import {ConnectionLostError} from "@web/core/network/rpc";
import {ProductScreen} from "@point_of_sale/app/screens/product_screen/product_screen";
import {definePosModels} from "@point_of_sale/../tests/unit/data/generate_model_definitions";
import {mountPosDialog, setupPosEnv} from "@point_of_sale/../tests/unit/utils";
import {ShopStockPopup} from "@deltatech_pos_stock_shops/js/shop_stock_popup.esm";

definePosModels();

const SHOP_B = 2;
const SHOP_C = 3;

/**
 * Template 5: in stock here only. Template 6: out of stock here, 4 in shop B and -1 in shop C.
 * Template 1 (the tip) is not storable and must never pass a stock filter.
 */
async function setupShops() {
    const store = await setupPosEnv();
    Object.assign(store.config, {
        display_stock: true,
        display_shop_stock: true,
        stock_badge_quantity: "on_hand",
        stock_shop_list: [
            {id: SHOP_B, name: "Shop B"},
            {id: SHOP_C, name: "Shop C"},
        ],
    });
    const here = store.models["product.template"].get(5);
    Object.assign(here, {is_storable: true, qty_available: 3, pos_shop_stock: {}});
    const elsewhere = store.models["product.template"].get(6);
    Object.assign(elsewhere, {
        is_storable: true,
        qty_available: 0,
        pos_shop_stock: {[SHOP_B]: 4, [SHOP_C]: -1},
    });
    return {store, here, elsewhere};
}

const displayedIds = (store) => store.productsToDisplay.map((product) => product.id);

describe("deltatech_pos_stock_shops", () => {
    test("the filter keeps the stock of this shop or of the other shops", async () => {
        const {store, here, elsewhere} = await setupShops();

        store.setShopStockFilter("here");
        expect(displayedIds(store)).toInclude(here.id);
        expect(displayedIds(store)).not.toInclude(elsewhere.id);
        expect(displayedIds(store)).not.toInclude(1);

        store.setShopStockFilter("shops");
        expect(displayedIds(store)).toInclude(elsewhere.id);
        expect(displayedIds(store)).not.toInclude(here.id);

        // A second tap takes the filter off.
        store.setShopStockFilter("shops");
        expect(store.shopStockFilter).toBe("all");
        expect(displayedIds(store)).toInclude(here.id);
        expect(displayedIds(store)).toInclude(elsewhere.id);
    });

    test("the filter does nothing when the other shops are not shown", async () => {
        const {store, here, elsewhere} = await setupShops();
        store.config.stock_shop_list = [];

        store.setShopStockFilter("shops");
        expect(displayedIds(store)).toInclude(here.id);
        expect(displayedIds(store)).toInclude(elsewhere.id);
    });

    test("the card shows what the other shops have, negative stock left out", async () => {
        const {store, elsewhere} = await setupShops();
        store.addNewOrder();
        await mountWithCleanup(ProductScreen, {props: {orderUuid: store.getOrder().uuid}});

        expect(`article[data-product-id="${elsewhere.id}"] .product-shop-qty`).toHaveText("+4");
        expect(".product-shop-qty").toHaveCount(1);

        await click(".o_pos_shop_stock_filter button[data-filter='shops']");
        await animationFrame();
        expect(".o_pos_shop_stock_filter button[data-filter='shops']").toHaveClass("btn-primary");
        expect(store.shopStockFilter).toBe("shops");
    });

    test("the product info keeps this shop and the chosen shops only", async () => {
        const {store, elsewhere} = await setupShops();
        store.addNewOrder();
        onRpc("product.template", "get_product_info_pos", () => ({
            all_prices: {tax_details: []},
            pricelists: [],
            warehouses: [
                {id: 1, name: "Shop A"},
                {id: 9, name: "Central warehouse"},
                {id: SHOP_B, name: "Shop B"},
            ],
            suppliers: [],
            variants: [],
            optional_products: [],
        }));

        const info = await store.getProductInfo(elsewhere, 1);
        expect(info.productInfo.warehouses.map((w) => w.id)).toEqual([1, SHOP_B]);
    });

    test("offline, the product info falls back on the stock loaded with the session", async () => {
        const {store, elsewhere} = await setupShops();
        store.addNewOrder();
        patchWithCleanup(store, {
            async getProductInfo() {
                throw new ConnectionLostError("/web/dataset/call_kw");
            },
        });
        const opened = [];
        patchWithCleanup(store.dialog, {
            add(component, props) {
                opened.push([component, props]);
            },
        });

        await store.onProductInfoClick(elsewhere);
        expect(opened).toHaveLength(1);
        expect(opened[0][0]).toBe(ShopStockPopup);
        expect(opened[0][1].productTemplate).toBe(elsewhere);
    });

    test("the offline popup lists this shop and every other shop", async () => {
        const {elsewhere} = await setupShops();
        const popup = await mountPosDialog(ShopStockPopup, {productTemplate: elsewhere, close: () => null});

        expect(popup.rows.map((row) => [row.name, row.quantity]).slice(1)).toEqual([
            ["Shop B", 4],
            ["Shop C", -1],
        ]);
        expect(popup.rows[0].isCurrent).toBe(true);
        expect(".o_pos_shop_stock_popup tbody tr").toHaveCount(3);
    });
});
