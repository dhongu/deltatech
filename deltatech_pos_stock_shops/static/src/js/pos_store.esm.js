/** @odoo-module **/

import {PosStore} from "@point_of_sale/app/services/pos_store";
import {ConnectionLostError} from "@web/core/network/rpc";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";
import {ShopStockPopup} from "./shop_stock_popup.esm";
import {hasShopStock, localStockQuantity, shopStockTotal} from "./shop_stock_utils.esm";

patch(PosStore.prototype, {
    async setup() {
        // Set before anything renders, so the product list subscribes to it.
        this.shopStockFilter = "all";
        return await super.setup(...arguments);
    },

    get shopStockFilterOptions() {
        return [
            {value: "all", label: _t("All products")},
            {value: "here", label: _t("In stock here")},
            {value: "shops", label: _t("In other shops")},
        ];
    },

    setShopStockFilter(value) {
        // A second tap on the active filter takes it off.
        this.shopStockFilter = value === this.shopStockFilter ? "all" : value;
    },

    filterExcludedProducts(products) {
        const mode = this.shopStockFilter;
        if (!mode || mode === "all" || !hasShopStock(this.config)) {
            return super.filterExcludedProducts(products);
        }
        // Filtered before the core loop, which stops at the first 100 products it keeps:
        // filtering its result instead would leave a near-empty page.
        return super.filterExcludedProducts(this._iterShopStockProducts(products, mode));
    },

    *_iterShopStockProducts(products, mode) {
        for (const product of products) {
            if (this._matchesShopStockFilter(product, mode)) {
                yield product;
            }
        }
    },

    _matchesShopStockFilter(product, mode) {
        if (!product.is_storable) {
            return false;
        }
        if (mode === "here") {
            return localStockQuantity(this.config, product) > 0;
        }
        return shopStockTotal(this.config, product) > 0;
    },

    async getProductInfo() {
        const info = await super.getProductInfo(...arguments);
        const warehouses = info?.productInfo?.warehouses;
        if (warehouses?.length && hasShopStock(this.config)) {
            // The server lists every warehouse of the company, the shop of the register first.
            // Keep that one and the shops chosen on the register: the central warehouse or a
            // transit location is not something a cashier can hand over.
            const shopIds = new Set(this.config.stock_shop_list.map((shop) => shop.id));
            info.productInfo.warehouses = warehouses.filter(
                (warehouse, index) => index === 0 || shopIds.has(warehouse.id)
            );
        }
        return info;
    },

    async onProductInfoClick(productTemplate) {
        try {
            return await super.onProductInfoClick(...arguments);
        } catch (error) {
            if (error instanceof ConnectionLostError && hasShopStock(this.config)) {
                this.dialog.add(ShopStockPopup, {productTemplate});
                return;
            }
            throw error;
        }
    },
});
