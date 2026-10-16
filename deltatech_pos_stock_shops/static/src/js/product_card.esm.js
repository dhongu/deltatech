/** @odoo-module **/

import {ProductCard} from "@point_of_sale/app/components/product_card/product_card";
import {patch} from "@web/core/utils/patch";
import {hasShopStock, shopStockTotal} from "./shop_stock_utils.esm";

// `this.pos` is set by the patch of deltatech_pos_stock.
patch(ProductCard.prototype, {
    get shopStockTotal() {
        if (!hasShopStock(this.pos?.config)) {
            return 0;
        }
        return shopStockTotal(this.pos.config, this.props.product);
    },
});
