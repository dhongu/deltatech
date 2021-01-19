odoo.define("deltatech_website_delivery_and_payment.checkout", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");
    require("website_sale_delivery.checkout");
    var websiteSaleDelivery = publicWidget.registry.websiteSaleDelivery;

    var concurrency = require("web.concurrency");
    var dp = new concurrency.DropPrevious();

    // PublicWidget.registry.websiteSaleDeliveryConstrain = publicWidget.Widget.extend({
    websiteSaleDelivery.include({
        selector: ".oe_website_sale",
        events: _.extend({}, websiteSaleDelivery.prototype.events, {
            //   "click #delivery_carrier .o_delivery_carrier_select": "_onCarrierClick",
            "click #payment_method .o_payment_acquirer_select": "_onAcquirerClickCheck",
        }),

        /**
         * @override
         */
        start: function () {
            return this._super.apply(this, arguments);
        },

        _handleCarrierCheckResult: function (result) {
            var $payButton = $("#o_payment_form_pay");
            if (result.status === true) {
                $payButton.data("disabled_reasons").acquirer_selection = false;
                $payButton.prop("disabled", _.contains($payButton.data("disabled_reasons"), true));
            }
            var $acquirers = $('#payment_method input[name="pm_id"]');
            if (result.all_acquirer === false) {
                $acquirers.each(function (index, acquirer) {
                    var acquirer_id = $(acquirer).data("acquirer-id");
                    if (result.acquirer_allowed_ids.includes(acquirer_id)) {
                        $(acquirer).parent().parent().show();
                        $(acquirer).parent().show();
                        $(acquirer).show();
                    } else {
                        $(acquirer).parent().parent().hide();
                        $(acquirer).parent().hide();
                        $(acquirer).hide();
                    }
                });
            } else {
                $acquirers.each(function (index, acquirer) {
                    $(acquirer).parent().parent().show();
                    $(acquirer).parent().show();
                    $(acquirer).show();
                });
            }
        },

        _doCheckSelection: function () {
            var self = this;
            var $carrier = $('#delivery_carrier input[name="delivery_type"]').filter(":checked");
            var carrier_id = $carrier.val();
            // Var $radio = $(ev.currentTarget).find('input[type="radio"]');
            // var carrier_id =  $radio.val();
            var $acquirer = $('#payment_method input[name="pm_id"]').filter(":checked");
            var acquirer_id = $acquirer.data("acquirer-id");

            var $payButton = $("#o_payment_form_pay");
            $payButton.prop("disabled", true);
            $payButton.data("disabled_reasons", $payButton.data("disabled_reasons") || {});
            $payButton.data("disabled_reasons").acquirer_selection = true;

            // Se verifica daca combinatia este permisa
            self._rpc({
                route: "/shop/carrier_acquirer_check",
                params: {
                    carrier_id: carrier_id,
                    acquirer_id: acquirer_id,
                },
            }).then(self._handleCarrierCheckResult.bind(self));
        },

        _onCarrierClick: function () {
            this._super.apply(this, arguments);
            var $acquirer = $('#payment_method input[name="pm_id"]').filter(":checked");
            $acquirer.prop("checked", false);

            this._doCheckSelection();
        },

        _onAcquirerClickCheck: function () {
            this._doCheckSelection();

            var $carrier = $('#delivery_carrier input[name="delivery_type"]').filter(":checked");
            var carrier_id = $carrier.val();
            dp.add(
                this._rpc({
                    route: "/shop/update_carrier",
                    params: {
                        carrier_id: carrier_id,
                    },
                })
            ).then(this._handleCarrierUpdateResult.bind(this));
        },
    });
});
