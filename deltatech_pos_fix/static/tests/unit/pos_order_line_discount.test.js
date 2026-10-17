import {describe, expect, test} from "@odoo/hoot";
import {definePosModels} from "@point_of_sale/../tests/unit/data/generate_model_definitions";
import {setupPosEnv} from "@point_of_sale/../tests/unit/utils";

definePosModels();

/**
 * Fiscal position 1 maps B -> C. The global discount line (pos_discount) already carries the
 * mapped taxes of the lines it discounts, so it must not be mapped a second time.
 */
async function setupDiscountMapping() {
    const store = await setupPosEnv();
    const models = store.models;
    const taxB = models["account.tax"].create({id: 31, name: "B 30%", amount_type: "percent", amount: 30});
    const taxC = models["account.tax"].create({id: 32, name: "C 40%", amount_type: "percent", amount: 40});
    const fp = models["account.fiscal.position"].get(1);
    fp.update({tax_map: {[taxB.id]: [taxC.id]}});
    const discountProduct = models["product.template"].get(5).product_variant_ids[0];
    const regularProduct = models["product.template"].get(6).product_variant_ids[0];
    store.config.discount_product_id = discountProduct;
    const order = store.addNewOrder();
    order.fiscal_position_id = fp;
    const makeLine = (product) =>
        models["pos.order.line"].create({
            order_id: order,
            product_id: product,
            price_unit: 10,
            qty: 1,
            tax_ids: [taxB],
        });
    return {taxB, taxC, discountLine: makeLine(discountProduct), regularLine: makeLine(regularProduct)};
}

const taxIdsOf = (line) => line.prepareBaseLineForTaxesComputationExtraValues().tax_ids.map((tax) => tax.id);

describe("deltatech_pos_fix", () => {
    test("a regular line is mapped through the fiscal position", async () => {
        const {taxC, regularLine} = await setupDiscountMapping();
        expect(taxIdsOf(regularLine)).toEqual([taxC.id]);
    });

    test("the global discount line keeps its already mapped taxes", async () => {
        const {taxB, discountLine} = await setupDiscountMapping();
        expect(taxIdsOf(discountLine)).toEqual([taxB.id]);
        expect(discountLine.prepareBaseLineForTaxesComputationExtraValues().price_unit).toBe(10);
    });
});
