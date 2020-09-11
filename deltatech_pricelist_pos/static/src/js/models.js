odoo.define("deltatech_pricelist_pos.model", function(require) {
    "use strict";

    var posmodel;
    var models = require("point_of_sale.models");
    var utils = require("web.utils");
    var round_pr = utils.round_precision;

    models.load_fields("product.product", ["currency_id"]);
    models.load_fields("res.company", ["price_currency_id"]);

    var _super_pos = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function(session, attributes) {
            _super_pos.initialize.call(this, session, attributes);
            var self = this;
            posmodel = this;
            this.fix_model_currency();
        },
        // Redefinirea mode de citire currency
        fix_model_currency: function() {
            for (var i = 0; i < this.models.length; i++) {
                var model = this.models[i];
                if (model.model === "res.currency") {
                    model.ids = function(self) {
                        return [
                            self.config.currency_id[0],
                            self.company.currency_id[0],
                            self.company.price_currency_id[0],
                        ];
                    };
                    model.loaded = function(self, currencies) {
                        self.currency = currencies[0];
                        if (self.currency.rounding > 0 && self.currency.rounding < 1) {
                            self.currency.decimals = Math.ceil(Math.log(1.0 / self.currency.rounding) / Math.log(10));
                        } else {
                            self.currency.decimals = 0;
                        }

                        self.company_currency = currencies[1];
                        self.price_currency = currencies[2];
                    };
                }
            }
        },
    });

    var _super_product = models.Product.prototype;
    models.Product = models.Product.extend({
        initialize: function(attr, options) {
            _super_product.initialize.call(this, attr, options);
        },

        get_price: function(pricelist, quantity) {
            var self = this;
            var price;
            price = _super_product.get_price.call(this, pricelist, quantity);
            if (self.currency_id[0] === posmodel.price_currency.id) {
                var conversion_rate = posmodel.currency.rate / posmodel.price_currency.rate;
                price = round_pr(price * conversion_rate, posmodel.currency.rounding);
            }
            return price;
        },
    });
});
