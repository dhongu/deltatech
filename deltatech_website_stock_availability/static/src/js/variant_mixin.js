odoo.define("deltatech_website_stock_availability.VariantMixin", function (require) {
    "use strict";

    var VariantMixin = require("sale.VariantMixin");
    var ajax = require("web.ajax");
    var core = require("web.core");
    var QWeb = core.qweb;
    var xml_load = ajax.loadXML(
        "/deltatech_website_stock_availability/static/src/xml/website_sale_stock_product_availability.xml",
        QWeb
    );

    const originalOnChangeCombination = VariantMixin._onChangeCombination;

    VariantMixin._onChangeCombination = function (ev, $parent, combination) {
        var product_id = 0;
        // Needed for list view of variants
        if ($parent.find("input.product_id:checked").length) {
            product_id = $parent.find("input.product_id:checked").val();
        } else {
            product_id = $parent.find(".product_id").val();
        }
        var isMainProduct =
            combination.product_id &&
            ($parent.is(".js_main_product") || $parent.is(".main_product")) &&
            combination.product_id === parseInt(product_id, 10);

        if (this.isWebsite && isMainProduct) {
            var qty = $parent.find('input[name="add_qty"]').val();
            combination.selected_qty = qty;
            if (combination.product_type === "product") {
                xml_load.then(function () {
                    $(".oe_website_sale")
                        .find(".lead_time_messages_" + combination.product_template)
                        .remove();

                    var $message = $(QWeb.render("deltatech_website_stock_availability.lead_time", combination));
                    $("div.lead_time_messages").html($message);
                });
            }
        }
        originalOnChangeCombination.apply(this, [ev, $parent, combination]);
    };

    return VariantMixin;
});
