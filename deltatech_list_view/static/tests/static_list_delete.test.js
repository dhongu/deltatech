import {expect, test} from "@odoo/hoot";
import {pointerDown, press, queryOne} from "@odoo/hoot-dom";
import {animationFrame} from "@odoo/hoot-mock";
import {contains, defineModels, fields, models, mountView, onRpc} from "@web/../tests/web_test_helpers";

class ReturnLine extends models.Model {
    _name = "return.line";
    name = fields.Char();
}

class ReturnWizard extends models.Model {
    _name = "return.wizard";
    // Like stock.return.picking: the lines of a new wizard come from the server, unsaved
    line_ids = fields.One2many({
        relation: "return.line",
        default: [
            [0, 0, {name: "A"}],
            [0, 0, {name: "B"}],
        ],
    });
}

defineModels([ReturnLine, ReturnWizard]);

test("Enter twice on the trash of an unsaved line sends no DELETE", async () => {
    onRpc("web_save", ({args}) => {
        expect.step("web_save");
        const commands = args[1].line_ids;
        // A DELETE with a virtual id reaches SQL as `DELETE ... WHERE id IN ('virtual_N')`
        expect(commands.filter((c) => c[0] === 2)).toEqual([]);
        expect(commands.map((c) => c[2]?.name)).toEqual(["B"]);
    });
    await mountView({
        type: "form",
        resModel: "return.wizard",
        arch: `
            <form>
                <field name="line_ids">
                    <list editable="bottom"><field name="name"/></list>
                </field>
            </form>`,
    });
    expect(".o_data_row").toHaveCount(2);
    // The trash cell reached with the keyboard: Enter has no guard against repeats, unlike the click
    await pointerDown(".o_data_row:first-child .o_list_record_remove");
    expect(queryOne(".o_data_row:first-child .o_list_record_remove")).toBeFocused();
    // Second Enter before the list re-renders: both deletes queue on the model mutex
    press("Enter");
    press("Enter");
    await animationFrame();
    expect(".o_data_row").toHaveCount(1);
    await contains(".o_form_button_save").click();
    expect.verifySteps(["web_save"]);
});
