odoo.define("deltatech_alternative_barcode.picking_client_action", function (require) {
    "use strict";

    var ClientAction = require("stock_barcode.ClientAction");

    ClientAction.include({
        _getProductByBarcode: async function (barcode) {
            let product = await this._super.apply(this, arguments);
            if (product) {
                return product;
            }
            product = await this._rpc({
                model: "product.product",
                method: "search_read",
                args: [[["alternative_ids.name", "=", barcode]], ["barcode", "display_name", "uom_id", "tracking"]],
            });
            if (product.length) {
                this.productsByBarcode[barcode] = product[0];
                return product[0];
            }
            return false;
        },
    });
});
