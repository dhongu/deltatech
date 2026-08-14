/** @odoo-module **/

import {ProductCard} from "@point_of_sale/app/components/product_card/product_card";
import {usePos} from "@point_of_sale/app/hooks/pos_hook";
import {patch} from "@web/core/utils/patch";
import {formatCurrency} from "@web/core/currency";

patch(ProductCard.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
    },
    get formattedPrice() {
        if (!this.pos?.config?.display_price || !this.props.product) {
            return "";
        }
        try {
            // În 19.0 nu mai există `pos.getProductPriceFormatted`; prețul afișat se calculează
            // din detaliile de taxe ale șablonului de produs, respectând setarea `iface_tax_included`.
            const config = this.pos.config;
            const order = this.pos.getOrder();
            const taxDetails = this.props.product.getTaxDetails({
                overridedValues: {
                    pricelist: order?.pricelist_id || config.pricelist_id,
                    fiscalPosition: order?.fiscal_position_id || false,
                },
            });
            const price = config.iface_tax_included === "total" ? taxDetails.total_included : taxDetails.total_excluded;
            return formatCurrency(price, config.currency_id.id);
        } catch (e) {
            console.error("Error formatting price:", e);
            return "";
        }
    },
});
