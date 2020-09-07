odoo.define("deltatech_website_delivery_and_payment.checkout", function(require) {
    "use strict";

    var publicWidget = require("web.public.widget");

    publicWidget.registry.websiteSaleDeliveryConstrain = publicWidget.Widget.extend({
        selector: ".oe_website_sale",
        events: {
            "click #delivery_carrier .o_delivery_carrier_select": "_onCarrierClick",
            "click #payment_method .o_payment_acquirer_select": "_onAcquirerClick",
        },

        /**
         * @override
         */
        start: function() {
            return this._super.apply(this, arguments);
        },

        _handleCarrierCheckResult: function(result) {
            var $payButton = $("#o_payment_form_pay");
            if (result.status === true) {
                $payButton.data("disabled_reasons").acquirer_selection = false;
                $payButton.prop("disabled", _.contains($payButton.data("disabled_reasons"), true));
            }
        },

        _doCheckSelection: function() {
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

        _onCarrierClick: function() {
            this._doCheckSelection();
        },

        _onAcquirerClick: function() {
            this._doCheckSelection();
        },
    });
});
