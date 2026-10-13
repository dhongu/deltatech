import {CustomerAddress} from "@portal/interactions/address";
import {patch} from "@web/core/utils/patch";
import {patchDynamicContent} from "@web/public/utils";
import {rpc} from "@web/core/network/rpc";

patch(CustomerAddress.prototype, {
    setup() {
        super.setup();
        patchDynamicContent(this.dynamicContent, {
            'select[name="city_id"]': {"t-on-change": this.onChangeCity.bind(this)},
        });

        this.elementState = this.addressForm.state_id;
        this.elementCities = this.addressForm.city_id;

        // Reordonăm câmpurile: țară → județ → localitate → stradă
        this._reorderAddressFields();

        // Verificăm la start dacă trebuie ascuns city
        this._toggleCityFields();
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

    _changeOption(selectElement, choices) {
        // Empty existing options, only keep the placeholder.
        selectElement.options.length = 1;
        if (choices.length) {
            choices.forEach((item) => {
                const option = new Option(item[1], item[0]);
                option.setAttribute("data-code", item[2]);
                selectElement.appendChild(option);
            });
        }
    },

    async onChangeState() {
        await this.waitFor(super.onChangeState());
        const stateId = this.elementState.value;
        let choices = [];
        if (stateId) {
            // The address type tells the server whether the courier's locality
            // catalog applies: it only restricts the delivery address.
            const data = await this.waitFor(
                rpc(`/portal/state_infos/${stateId}`, {
                    address_type: this.addressForm.address_type?.value || "billing",
                    use_delivery_as_billing: this.addressForm.use_delivery_as_billing?.value || false,
                })
            );
            choices = data.cities;
        }
        this._changeOption(this.elementCities, choices);

        this._toggleCityFields();
        await this.onChangeCity();
    },

    _toggleCityFields() {
        // Dacă city_id are opțiuni și valoare, ascundem city (input text)
        if (this.elementCities && this.elementCities.options.length > 1) {
            this._hideInput("city");
            this._showInput("city_id");
        } else {
            this._hideInput("city_id");
            this._showInput("city");
        }
    },

    async _onChangeCountry() {
        await this.waitFor(super._onChangeCountry(...arguments));
        this._toggleCityFields();
    },

    async onChangeCity() {
        // Clear free-text city when a city_id is selected
        const cityInput = this.addressForm.city;
        if (cityInput && cityInput.value) {
            cityInput.value = "";
        }
        // Auto-fill ZIP/postal code based on selected city's code (if provided)
        const zipInput = this.addressForm.zip;
        if (this.elementCities) {
            const selectedOption = this.elementCities.options[this.elementCities.selectedIndex];
            const cityZip = selectedOption ? selectedOption.getAttribute("data-code") : "";
            if (zipInput) {
                if (cityZip) {
                    zipInput.value = cityZip;
                    // Mirror runtime value into attribute so CSS selectors in tours can match
                    zipInput.setAttribute("value", cityZip);
                } else if (!this.elementCities.value) {
                    // If no city selected, clear zip to let user enter manually
                    zipInput.value = "";
                    zipInput.setAttribute("value", "");
                }
            }
        }
    },
});
