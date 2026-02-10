/** @odoo-module **/

import portalDetails from "@portal/js/portal";
import {rpc} from "@web/core/network/rpc";

portalDetails.include({
    events: Object.assign({}, portalDetails.prototype.events, {
        "change select[name='state_id']": "_onChangeState",
        "change select[name='city_id']": "_onChangeCity",
    }),

    start() {
        this.$city_id = this.$('select[name="city_id"]');
        this.$state_id = this.$('select[name="state_id"]');
        this.$city = this.$('input[name="city"]');

        this.elementCities = this.$city_id[0];
        this.elementState = this.$state_id[0];
        this.elementCityText = this.$city[0];

        // Initialize cities list if a state is already selected, else just toggle
        if (this.elementState && this.elementState.value) {
            this._onChangeState();
        } else {
            this._toggleCityFields();
        }

        return this._super(...arguments);
    },

    _toggleCityFields() {
        if (this.elementCities && this.elementCities.options.length > 1) {
            this._hideInput("city");
            if (this.elementCityText) {
                this.elementCityText.disabled = true;
                this.elementCityText.removeAttribute("required");
                this.elementCityText.classList.remove("is-invalid");
                // Sync city text with selected city_id name if city_id has a value
                const selectedOption = this.elementCities.options[this.elementCities.selectedIndex];
                if (selectedOption && selectedOption.value) {
                    this.elementCityText.value = selectedOption.text;
                }
            }

            this._showInput("city_id");
            if (this.elementCities) {
                this.elementCities.disabled = false;
                this.elementCities.setAttribute("required", "");
                this.elementCities.classList.remove("is-invalid");
            }
        } else {
            this._hideInput("city_id");
            if (this.elementCities) {
                this.elementCities.disabled = true;
                this.elementCities.removeAttribute("required");
                this.elementCities.classList.remove("is-invalid");
            }

            this._showInput("city");
            if (this.elementCityText) {
                this.elementCityText.disabled = false;
                this.elementCityText.setAttribute("required", "");
                this.elementCityText.classList.remove("is-invalid");
            }
        }
    },

    _hideInput(name) {
        if (!this.el) return;
        const div = this.el.querySelector("#div_" + name);
        if (div) {
            div.classList.add("d-none");
        }
    },

    _showInput(name) {
        if (!this.el) return;
        const div = this.el.querySelector("#div_" + name);
        if (div) {
            div.classList.remove("d-none");
        }
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
            // Restore selection from server-rendered value if present
            const currentId = this.elementCities.dataset.current_city_id;
            if (currentId) {
                this.elementCities.value = currentId;
            }
        }
        this._toggleCityFields();
    },

    async _onChangeCity() {
        if (this.elementCities && this.elementCityText) {
            const selectedOption = this.elementCities.options[this.elementCities.selectedIndex];
            if (selectedOption && selectedOption.value) {
                this.elementCityText.value = selectedOption.text;
            } else {
                this.elementCityText.value = "";
            }
        }
    },
});
