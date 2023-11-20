odoo.define("deltatech_website_delivery_and_payment.checkout", function (require) {
    "use strict";

    var publicWidget = require("web.public.widget");
    require("website_sale_delivery.checkout");
    var websiteSaleDelivery = publicWidget.registry.websiteSaleDelivery;

    var concurrency = require("web.concurrency");
    var dp = new concurrency.DropPrevious();

    websiteSaleDelivery.include({
        selector: ".oe_website_sale",
        events: _.extend({}, websiteSaleDelivery.prototype.events, {
            //   "click #delivery_carrier .o_delivery_carrier_select": "_onCarrierClick",
            "click #payment_method .o_payment_option_card": "_onAcquirerClickCheck",
        }),

        /**
         * @override
         */
        start: function () {
            return this._super.apply(this, arguments);
        },

        _handleCarrierCheckResult: function (result) {
            var $payButton = this.$('button[name="o_payment_submit_button"]');

            var disabledReasons = $payButton.data("disabled_reasons") || {};
            disabledReasons.acquirer_cannot_be_selected = !result.status;
            $payButton.data("disabled_reasons", disabledReasons);

            var $acquirers = $('input[name="o_payment_radio"]');
            if (result.all_acquirer === false) {
                $acquirers.each(function (index, acquirer) {
                    var provider_id = $(acquirer).data("payment-option-id");
                    if (result.acquirer_allowed_ids.includes(provider_id)) {
                        $(acquirer).parent().parent().show();
                        $(acquirer).parent().show();
                        $(acquirer).show();
                    } else {
                        $(acquirer).parent().parent().hide();
                        $(acquirer).parent().hide();
                        $(acquirer).hide();
                        $(acquirer).prop("checked", false);
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
            if (!carrier_id) {
                return;
            }
            // Var $radio = $(ev.currentTarget).find('input[type="radio"]');
            // var carrier_id =  $radio.val();
            var $acquirer = $('#payment_method input[name="o_payment_radio"]').filter(":checked");
            var provider_id = $acquirer.data("payment-option-id");

            // Var $payButton = $("#o_payment_form_pay");
            var $payButton = this.$('button[name="o_payment_submit_button"]');
            $payButton.prop("disabled", true);

            var disabledReasons = $payButton.data("disabled_reasons") || {};
            disabledReasons.acquirer_selection = false;
            $payButton.data("disabled_reasons", disabledReasons);

            // $payButton.data("disabled_reasons", $payButton.data("disabled_reasons") || {});

            // $payButton.data("disabled_reasons").acquirer_selection = true;

            // Se verifica daca combinatia este permisa
            self._rpc({
                route: "/shop/carrier_acquirer_check",
                params: {
                    carrier_id: carrier_id,
                    provider_id: provider_id,
                },
            }).then(self._handleCarrierCheckResult.bind(self));
        },

        _onCarrierClick: function () {
            this._super.apply(this, arguments);
            // Var $acquirer = $('#payment_method input[name="o_payment_radio"]').filter(":checked");
            // $acquirer.prop("checked", false);
            //
            this._doCheckSelection();
        },

        _onAcquirerClickCheck: function () {
            this._doCheckSelection();
            var $acquirer = $('#payment_method input[name="o_payment_radio"]').filter(":checked");
            var provider_id = $acquirer.data("payment-option-id");
            var $carrier = $('#delivery_carrier input[name="delivery_type"]').filter(":checked");
            var carrier_id = $carrier.val();
            if (!carrier_id) {
                return;
            }
            dp.add(
                this._rpc({
                    route: "/shop/carrier_rate_shipment",
                    params: {
                        carrier_id: carrier_id,
                        provider_id: provider_id,
                    },
                })
            ).then(this._handleCarrierUpdateResult.bind(this));
        },
    });
});
