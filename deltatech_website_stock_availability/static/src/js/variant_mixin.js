odoo.define("deltatech_website_stock_availability.VariantMixin", function (require) {
    "use strict";

    var VariantMixin = require("sale.VariantMixin");
    var publicWidget = require("web.public.widget");

    var core = require("web.core");
    var QWeb = core.qweb;

    require("website_sale.website_sale");

    VariantMixin._onChangeLeadTimeMessage = function (ev, $parent, combination) {
        let product_id = 0;
        // Needed for list view of variants
        if ($parent.find("input.product_id:checked").length) {
            product_id = $parent.find("input.product_id:checked").val();
        } else {
            product_id = $parent.find(".product_id").val();
        }
        const isMainProduct =
            combination.product_id &&
            ($parent.is(".js_main_product") || $parent.is(".main_product")) &&
            combination.product_id === parseInt(product_id, 10);

        if (!this.isWebsite || !isMainProduct) {
            return;
        }

        const $addQtyInput = $parent.find('input[name="add_qty"]');
        const qty = $addQtyInput.val();
        combination.selected_qty = qty;

        $(".oe_website_sale")
            .find(".lead_time_messages_" + combination.product_template)
            .remove();
        const $message = $(QWeb.render("deltatech_website_stock_availability.lead_time", combination));

        $("div.lead_time_messages").html($message);
        // LoadXml().then(function () {
        //
        // });
    };

    publicWidget.registry.WebsiteSale.include({
        _onChangeCombination: function () {
            this._super.apply(this, arguments);
            VariantMixin._onChangeLeadTimeMessage.apply(this, arguments);
        },
    });

    return VariantMixin;
});
