import {describe, expect, test} from "@odoo/hoot";
import {definePosModels} from "@point_of_sale/../tests/unit/data/generate_model_definitions";
import {setupPosEnv} from "@point_of_sale/../tests/unit/utils";

definePosModels();

// The pos_hr fixtures: employee 2 is a manager, 3 a cashier, 4 restrictive, 5 supervised.
async function setupStore(employeeId, config) {
    const store = await setupPosEnv();
    Object.assign(store.config, config);
    store.setCashier(store.models["hr.employee"].get(employeeId));
    return store;
}

describe("@deltatech_pos_cashier_close close register", () => {
    test("a cashier closes the register when the register allows it", async () => {
        const store = await setupStore(3, {cashier_can_close: true});
        expect(store.accessRight.canCloseSession).toBe(true);
    });

    test("a cashier does not close it when the register does not allow it", async () => {
        const store = await setupStore(3, {cashier_can_close: false});
        expect(store.accessRight.canCloseSession).toBe(false);
    });

    test("restrictive employees never close the register", async () => {
        const store = await setupStore(4, {cashier_can_close: true});
        expect(store.accessRight.canCloseSession).toBe(false);
    });

    test("supervised employees never close the register", async () => {
        const store = await setupStore(5, {cashier_can_close: true});
        expect(store.accessRight.canCloseSession).toBe(false);
    });

    test("managers still close it, as in standard", async () => {
        const store = await setupStore(2, {cashier_can_close: false});
        expect(store.accessRight.canCloseSession).toBe(true);
    });

    test("the other manager rights stay with the managers", async () => {
        const store = await setupStore(3, {cashier_can_close: true});
        expect(store.accessRight.hasProductCreationAccess).toBe(false);
        expect(store.accessRight.canPrintReport).toBe(false);
        expect(store.accessRight.employeeIsAdmin).toBe(false);
    });
});
