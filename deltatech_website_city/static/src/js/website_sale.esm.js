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

        return this._super.apply(this, arguments);
    },
    _changeOption: function (selectCheck, rpcRoute, place, selectElement) {
        if (!selectCheck) {
            return;
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
                selectElement.parentElement.style.display = "block";
            } else {
                selectElement.value = "";
                selectElement.parentElement.style.display = "none";
            }
        });
    },
    _onChangeState: function () {
        if (this.elementState.value === "" && this.elemenCountry.value !== "") {
            this.elementState.options[1].selected = true;
        }
        const state = this.elementState.value;
        const rpcRoute = `/shop/state_infos/${state}`;
        return this.autoFormat.length
            ? this._changeOption(state, rpcRoute, "cities", this.elementCities) // .then(() => this._onChangeCity())
            : undefined;
    },

    _onChangeCity: function () {
        // Todo: de completat codul postal in functie de oras
    },

    _onChangeCountry: function () {
        return this._super.apply(this, arguments).then(() => {
            // Const selectedCountry = ev.currentTarget.options[ev.currentTarget.selectedIndex].getAttribute("code");
            const cityInput = document.querySelector(".form-control[name='city']");

            if (cityInput.value) {
                cityInput.value = "";
            }
            this.cityBlock.classList.add("d-none");
            return this._onChangeState(); // .then(() => {            this._onChangeCity();            });
        });
    },
});
