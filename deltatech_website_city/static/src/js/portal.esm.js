/** @odoo-module **/

import portalDetails from "@portal/js/portal";
import {rpc} from "@web/core/network/rpc";

portalDetails.include({
    events: Object.assign({}, portalDetails.prototype.events, {
        "change select[name='state_id']": "_onChangeState",
    }),

    start() {
        this.elementCities = document.querySelector("select[name='city_id']");
        this.elementState = document.querySelector("select[name='state_id']");
        return this._super(...arguments);
    },

    async _onChangeState() {
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
        } else {
        }
    },
});
