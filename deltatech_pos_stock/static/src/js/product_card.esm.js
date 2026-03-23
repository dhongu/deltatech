/** @odoo-module **/

import {ProductCard} from "@point_of_sale/app/generic_components/product_card/product_card";
import {usePos} from "@point_of_sale/app/store/pos_hook";
import {patch} from "@web/core/utils/patch";

patch(ProductCard.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
    },
    get formattedPrice() {
        if (this.pos && this.pos.config && this.pos.config.display_price && this.props.product) {
            try {
                return this.pos.getProductPriceFormatted(this.props.product);
            } catch (e) {
                console.error("Error formatting price:", e);
                return "";
            }
        }
        return "";
    },
});
