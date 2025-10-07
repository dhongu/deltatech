/** @odoo-module **/
import {WebsiteSale} from "@website_sale/js/website_sale";

WebsiteSale.include({
    events: Object.assign({}, WebsiteSale.prototype.events, {
        "change select[name='state_id']": "_onChangeState",
        "change select[name='city_id']": "_onChangeCity",
    }),
    start: function () {
        this.elementCities = document.querySelector("select[name='city_id']");
        this.cityBlock = document.querySelector(".div_city");
        this.zipBlock = document.querySelector(".div_zip");

        this.autoFormat = document.querySelector(".checkout_autoformat");
        this.elementState = document.querySelector("select[name='state_id']");
        this.elemenCountry = document.querySelector("select[name='country_id']");

        this.divCity = document.querySelector(".div_city");
        this.divCityId = document.querySelector(".div_city_id");

        // Reordonăm câmpurile: țară → județ → localitate → stradă
        this._reorderAddressFields();

        // Verificăm la start dacă trebuie ascuns city
        this._toggleCityFields();

        return this._super.apply(this, arguments);
    },

    _reorderAddressFields() {
        const divStreet = document.querySelector(".div_street");
        const divCountry = document.querySelector(".div_country");
        const divState = document.querySelector(".div_state");
        const divCityId = this.divCityId;
        const divCity = this.divCity;

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
        if (this.divCityId && this.divCity) {
            if (this.elementCities && this.elementCities.options.length > 1) {
                this.divCityId.classList.remove("d-none");
                this.divCity.classList.add("d-none");
            } else {
                this.divCityId.classList.add("d-none");
                this.divCity.classList.remove("d-none");
            }
        }
    },

    _changeOption: function (selectCheck, rpcRoute, place, selectElement) {
        if (!selectCheck) {
            return this._toggleCityFields();
        }
        return this.rpc(rpcRoute, {}).then((data) => {
            const data_place = data[place];
            if (data_place && data_place.length !== 0) {
                selectElement.innerHTML = "";
                data[place].forEach((item) => {
                    const opt = document.createElement("option");
                    opt.textContent = item[1];
                    opt.value = item[0];
                    opt.setAttribute("data-code", item[2]);
                    selectElement.appendChild(opt);
                });
            }
            this._toggleCityFields();
        });
    },
    _onChangeState: function () {
        if (this.elementState.value === "" && this.elemenCountry.value !== "") {
            this.elementState.options[1].selected = true;
        }
        const state = this.elementState.value;
        const rpcRoute = `/shop/state_infos/${state}`;
        return this.autoFormat.length ? this._changeOption(state, rpcRoute, "cities", this.elementCities) : undefined;
    },

    _onChangeCity: function () {
        // Todo: de completat codul postal in functie de oras
    },

    _onChangeCountry: function () {
        return this._super.apply(this, arguments).then(() => {
            return this._onChangeState();
        });
    },
});
