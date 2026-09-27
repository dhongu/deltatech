import {CustomerAddress} from "@portal/interactions/address";
import {patch} from "@web/core/utils/patch";
import {rpc} from "@web/core/network/rpc";

// In 20.0 the city dropdown is standard in `portal` (div_city_id, /my/address/state_info,
// ZIP filled from the chosen city). What stays here: the address type is sent along with the
// state, so the server can restrict the delivery address to the carrier's localities.
patch(CustomerAddress.prototype, {
    async onChangeState() {
        const data = await this.waitFor(
            rpc("/my/address/state_info", {
                country_id: parseInt(this.addressForm.country_id.value, 10),
                state_id: parseInt(this.addressForm.state_id.value, 10),
                address_type: this.addressType,
                use_delivery_as_billing: this.useDeliveryAsBilling,
            })
        );
        if (data.cities) {
            this._setFieldChoices("city_id", data.cities);
        }
        return data;
    },

    async onChangeCity() {
        await super.onChangeCity();
        // No city chosen: clear the ZIP filled from the previous one, to let the user type it.
        const zipInput = this.addressForm.zip;
        if (zipInput && this.addressForm.city_id && !this.addressForm.city_id.value) {
            zipInput.value = "";
        }
    },
});
