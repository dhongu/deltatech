/** @odoo-module **/

import {PosOrderline} from "@point_of_sale/app/models/pos_order_line";
import {patch} from "@web/core/utils/patch";
import {getTaxesAfterFiscalPosition} from "@point_of_sale/app/models/utils/tax_utils";
import {accountTaxHelpers} from "@account/helpers/account_tax";

patch(PosOrderline.prototype, {
    prepareBaseLineForTaxesComputationExtraValues() {
        const values = super.prepareBaseLineForTaxesComputationExtraValues(...arguments);
        const order = this.order_id;
        const product = this.get_product();
        const product_uom = this.get_unit();

        // Dacă există o poziție fiscală, trebuie să adaptăm prețul unitar
        // dacă taxele originale sunt incluse în preț și taxele noi nu sunt (sau invers).
        if (order.fiscal_position_id) {
            const original_taxes = this.tax_ids || product.taxes_id;
            const taxes_after_fp = getTaxesAfterFiscalPosition(original_taxes, order.fiscal_position_id, order.models);

            // Adapt_price_unit_to_another_taxes se ocupă de recalcularea prețului unitar
            // pentru a reflecta corect baza impozabilă în funcție de noile taxe.
            values.price_unit = accountTaxHelpers.adapt_price_unit_to_another_taxes(
                this.get_unit_price(),
                product,
                original_taxes,
                taxes_after_fp,
                {product_uom}
            );
            values.tax_ids = taxes_after_fp;
        }
        return values;
    },
});
