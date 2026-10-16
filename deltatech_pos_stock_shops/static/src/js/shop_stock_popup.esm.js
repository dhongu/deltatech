/** @odoo-module **/

import {Component} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";
import {usePos} from "@point_of_sale/app/hooks/pos_hook";
import {localStockQuantity, shopStockQuantity} from "./shop_stock_utils.esm";

/**
 * The stock per shop, built only from the data loaded with the session. Opened in place of the
 * standard product info popup when the server cannot be reached.
 */
export class ShopStockPopup extends Component {
    static template = "deltatech_pos_stock_shops.ShopStockPopup";
    static components = {Dialog};
    static props = ["productTemplate", "close"];

    setup() {
        this.pos = usePos();
    }

    get rows() {
        const config = this.pos.config;
        const product = this.props.productTemplate;
        const rows = [
            {
                id: "here",
                name: config.name,
                quantity: localStockQuantity(config, product),
                isCurrent: true,
            },
        ];
        for (const shop of config.stock_shop_list || []) {
            rows.push({
                id: shop.id,
                name: shop.name,
                quantity: shopStockQuantity(product, shop.id),
                isCurrent: false,
            });
        }
        return rows;
    }

    get uomName() {
        return this.props.productTemplate.uom_id?.name || "";
    }
}
