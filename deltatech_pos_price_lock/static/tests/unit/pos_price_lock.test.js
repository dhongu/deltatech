import {describe, expect, test} from "@odoo/hoot";
import {definePosModels} from "@point_of_sale/../tests/unit/data/generate_model_definitions";
import {patchWithCleanup} from "@web/../tests/web_test_helpers";
import {setupPosEnv} from "@point_of_sale/../tests/unit/utils";

definePosModels();

// User 2 (Administrator) is a POS manager in the point_of_sale fixtures.
async function setupStore(config) {
    const store = await setupPosEnv();
    Object.assign(store.config, {module_pos_hr: false, ...config});
    patchWithCleanup(store.accessRight, {
        get loggedCashier() {
            return this.data.models["res.users"].get(2);
        },
    });
    return store;
}

describe("@deltatech_pos_price_lock price control", () => {
    test("manager may change the price when only the standard restriction is on", async () => {
        const store = await setupStore({restrict_price_control: true, lock_price_for_managers: false});
        expect(store.accessRight.disablePriceButton).toBe(false);
    });

    test("manager may not change the price when the lock is on", async () => {
        const store = await setupStore({restrict_price_control: true, lock_price_for_managers: true});
        expect(store.accessRight.disablePriceButton).toBe(true);
    });

    test("the lock has no effect while the standard restriction is off", async () => {
        const store = await setupStore({restrict_price_control: false, lock_price_for_managers: true});
        expect(store.accessRight.disablePriceButton).toBe(false);
    });
});
