/** @odoo-module **/

import {rpc} from "@web/core/network/rpc";
import websiteSaleAddress from "@website_sale/js/address";

websiteSaleAddress.include({
    events: Object.assign({}, websiteSaleAddress.prototype.events, {
        "change select[name='state_id']": "_onChangeState",
        "change select[name='city_id']": "_onChangeCity",
    }),

    start: function () {
        this.elementCountry = this.addressForm.country_id;
        this.elementCities = this.addressForm.city_id;
        this.elementState = this.addressForm.state_id;

        this._changeCountry();

        // Reordonăm câmpurile: țară → județ → localitate → stradă
        this._reorderAddressFields();

        // Verificăm la start dacă trebuie ascuns city
        this._toggleCityFields();

        return this._super.apply(this, arguments);
    },

    _reorderAddressFields() {
        const divStreet = document.getElementById("div_street");
        const divCountry = document.getElementById("div_country");
        const divState = document.getElementById("div_state");
        const divCityId = document.getElementById("div_city_id");
        const divCity = document.getElementById("div_city");

        if (divStreet && divCountry && divState) {
            divCity.parentNode.insertBefore(divCountry, divCity);
            divCity.parentNode.insertBefore(divState, divCity);

            if (divCityId) {
                divCity.parentNode.insertBefore(divCityId, divCity);
            }
        }
    },

    _toggleCityFields() {
        // Dacă city_id are opțiuni și valoare, ascundem city (input text)
        if (this.elementCities && this.elementCities.options.length > 1) {
            this._hideInput("city");
            // Sincronizare atribute pentru validare HTML5
            this.addressForm.city.disabled = true;
            this.addressForm.city.removeAttribute("required");
            this.addressForm.city.classList.remove("is-invalid");
            this.addressForm.city.value = this.addressForm.city.value || "";

            this._showInput("city_id");
            this.addressForm.city_id.disabled = false;
            this.addressForm.city_id.setAttribute("required", "");
            this.addressForm.city_id.classList.remove("is-invalid");
        } else {
            this._hideInput("city_id");
            this.addressForm.city_id.disabled = true;
            this.addressForm.city_id.removeAttribute("required");
            this.addressForm.city_id.classList.remove("is-invalid");
            this.addressForm.city_id.value = this.addressForm.city_id.value || "";

            this._showInput("city");
            this.addressForm.city.disabled = false;
            this.addressForm.city.setAttribute("required", "");
            this.addressForm.city.classList.remove("is-invalid");
        }
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
            // This._hideInput("city");
            // this._showInput("city_id");
        } else {
            // This._hideInput("city_id");
            // this._showInput("city");
        }
        this._toggleCityFields();
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
        // După schimbarea țării, verificăm din nou vizibilitatea
        this._toggleCityFields();
    },
});
