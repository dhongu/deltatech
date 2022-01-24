odoo.define("deltatech_alternative_barcode.picking_client_action", function (require) {
    "use strict";

    var ClientAction = require("stock_barcode.ClientAction");

    ClientAction.include({
        _isProduct: async function () {
            var self = this;
            const product = await this._super.apply(this, arguments);
            if (product) {
                if (product.tracking === "lot" && self.requireLotNumber) {
                    self.requireLotNumber = false;
                    product.tracking = "none";
                }
            }
            return product;
        },

        _isAbleToCreateNewLine: function () {
            return false;
        },

        _incrementLines: function (params) {
            var product = params.product;
            if (product.tracking === "lot") {
                product.tracking = "none";
            }

            const values = this._super.apply(this, arguments);
            var line = values.lineDescription;
            if (params.barcode && line) {
                line.product_id.barcode = params.barcode;
                line.product_barcode = params.barcode;
            }

            return values;
        },

        _getProductByBarcode: async function (barcode) {
            let product = await this._super.apply(this, arguments);
            if (product) {
                return product;
            }
            const barcode_short = barcode.substring(1, barcode.length - 1);
            product = await this._rpc({
                model: "product.product",
                method: "search_read",
                args: [
                    [["alternative_ids.name", "in", [barcode, barcode_short]]],
                    ["barcode", "display_name", "uom_id", "tracking"],
                ],
            });
            if (product.length) {
                product[0].barcode = barcode;
                this.productsByBarcode[barcode] = product[0];
                return product[0];
            }
            return false;
        },
    });
});
