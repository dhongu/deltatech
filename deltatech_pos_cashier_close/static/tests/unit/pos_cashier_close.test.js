import {describe, expect, test} from "@odoo/hoot";
import {definePosModels} from "@point_of_sale/../tests/unit/data/generate_model_definitions";
import {Navbar} from "@point_of_sale/app/components/navbar/navbar";
import {mountWithCleanup} from "@web/../tests/web_test_helpers";
import {setupPosEnv} from "@point_of_sale/../tests/unit/utils";

definePosModels();

// The pos_hr fixtures: employee 2 is a manager, 3 a cashier, 4 has minimal rights.
async function mountNavbar(employeeId, config) {
    const store = await setupPosEnv();
    Object.assign(store.config, config);
    store.setCashier(store.models["hr.employee"].get(employeeId));
    // Not the user who opened the session, so the standard pos_hr rule does not grant it.
    store.session.user_id = undefined;
    return mountWithCleanup(Navbar, {});
}

describe("@deltatech_pos_cashier_close close register", () => {
    test("a cashier closes the register when the register allows it", async () => {
        const navbar = await mountNavbar(3, {cashier_can_close: true});
        expect(navbar.showCloseSession).toBe(true);
    });

    test("a cashier does not close it when the register does not allow it", async () => {
        const navbar = await mountNavbar(3, {cashier_can_close: false});
        expect(navbar.showCloseSession).toBe(false);
    });

    test("minimal rights never close the register", async () => {
        const navbar = await mountNavbar(4, {cashier_can_close: true});
        expect(navbar.showCloseSession).toBe(false);
    });

    test("managers still close it, as in standard", async () => {
        const navbar = await mountNavbar(2, {cashier_can_close: false});
        expect(navbar.showCloseSession).toBe(true);
    });

    test("the other manager rights stay with the managers", async () => {
        const navbar = await mountNavbar(3, {cashier_can_close: true});
        expect(navbar.showCreateProductButton).toBe(false);
        expect(navbar.pos.employeeIsAdmin).toBe(false);
    });
});
