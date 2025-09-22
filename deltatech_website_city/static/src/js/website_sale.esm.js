/** @odoo-module **/

import websiteSaleAddress from "@website_sale/js/address";
import {rpc} from "@web/core/network/rpc";

websiteSaleAddress.include({
    events: Object.assign({}, websiteSaleAddress.prototype.events, {
        "change select[name='state_id']": "_onChangeState",
        "change select[name='city_id']": "_onChangeCity",
    }),

    start: function () {
        this.elementCountry = this.addressForm.country_id;
        this.elementCities = this.addressForm.city_id;
        this.elementState = this.addressForm.state_id;
        return this._super.apply(this, arguments);
    },

    async _onChangeState() {
        await this._super(...arguments);
        const stateId = this.elementState.value;
        let choices = [];
        if (stateId) {
            const data = await rpc(`/shop/state_infos/${this.elementState.value}`, {});
            choices = data.cities;
        }
        this.elementCities.options.length = 1;
        if (choices.length) {
            choices.forEach((item) => {
                const option = new Option(item[1], item[0]);
                option.setAttribute("data-code", item[2]);
                this.elementCities.appendChild(option);
            });
            this._hideInput("city");
            this._showInput("city_id");
        } else {
            this._hideInput("city_id");
            this._showInput("city");
        }
    },

    async _onChangeCity() {
        // Const cityId = this.elementState.value;
        const cityInput = this.addressForm.city;
        if (cityInput.value) {
            cityInput.value = "";
        }
    },

    async _changeCountry() {
        await this._super(...arguments);
    },
});
