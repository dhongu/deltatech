import {describe, expect, test} from "@odoo/hoot";
import {definePosModels} from "@point_of_sale/../tests/unit/data/generate_model_definitions";
import {setupPosEnv} from "@point_of_sale/../tests/unit/utils";

definePosModels();

async function setupStore(config) {
    const store = await setupPosEnv();
    Object.assign(store.config, config);
    store.getCashier()._role = "manager";
    return store;
}

describe("@deltatech_pos_price_lock price control", () => {
    test("manager may change the price when only the standard restriction is on", async () => {
        const store = await setupStore({restrict_price_control: true, lock_price_for_managers: false});
        expect(store.cashierHasPriceControlRights()).toBe(true);
    });

    test("manager may not change the price when the lock is on", async () => {
        const store = await setupStore({restrict_price_control: true, lock_price_for_managers: true});
        expect(store.cashierHasPriceControlRights()).toBe(false);
    });

    test("the lock has no effect while the standard restriction is off", async () => {
        const store = await setupStore({restrict_price_control: false, lock_price_for_managers: true});
        expect(store.cashierHasPriceControlRights()).toBe(true);
    });
});
