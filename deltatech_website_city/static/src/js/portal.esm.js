/** @odoo-module **/

import portalDetails from "@portal/js/portal";
import {rpc} from "@web/core/network/rpc";

portalDetails.include({
    events: Object.assign({}, portalDetails.prototype.events, {
        "change select[name='state_id']": "_onChangeState",
    }),

    async start() {
        this.elementCities = document.querySelector("select[name='city_id']");
        this.elementState = document.querySelector("select[name='state_id']");
        this.elementCityText = document.querySelector("input[name='city']");

        const res = await this._super(...arguments);
        if (this.elementState && this.elementState.value) {
            await this._onChangeState();
        } else {
            this._toggleCityFields();
        }
        return res;
    },

    _toggleCityFields() {
        const divCity = document.getElementById("div_city");
        const divCityId = document.getElementById("div_city_id");

        if (this.elementCities && this.elementCities.options.length > 1) {
            if (divCity) divCity.style.display = "none";
            if (divCityId) divCityId.style.display = "";

            if (this.elementCityText) {
                this.elementCityText.disabled = true;
                this.elementCityText.removeAttribute("required");
            }
            if (this.elementCities) {
                this.elementCities.disabled = false;
                // This.elementCities.setAttribute("required", "");
            }
        } else {
            if (divCity) divCity.style.display = "";
            if (divCityId) divCityId.style.display = "none";

            if (this.elementCities) {
                this.elementCities.disabled = true;
                this.elementCities.removeAttribute("required");
            }
            if (this.elementCityText) {
                this.elementCityText.disabled = false;
                // This.elementCityText.setAttribute("required", "");
            }
        }
    },

    async _onChangeState() {
        if (!this.elementState || !this.elementCities) {
            return;
        }
        const stateId = this.elementState.value;
        let choices = [];
        if (stateId) {
            const data = await rpc(`/shop/state_infos/${stateId}`, {});
            choices = data.cities;
        }
        const currentCityId = this.elementCities.value || this.elementCities.dataset.value;
        this.elementCities.options.length = 1;
        if (choices.length) {
            choices.forEach((item) => {
                const option = new Option(item[1], item[0]);
                option.setAttribute("data-code", item[2]);
                if (String(item[0]) === String(currentCityId)) {
                    option.selected = true;
                }
                this.elementCities.appendChild(option);
            });
        }
        this._toggleCityFields();
    },
});
