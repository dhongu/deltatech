/** @odoo-module **/
import {describe, expect, test} from "@odoo/hoot";
import {click, resize, waitFor, waitForNone} from "@odoo/hoot-dom";
import {defineModels, fields, models, mountView, webModels} from "@web/../tests/web_test_helpers";
import "@deltatech_web_side_panel/side_panel/side_panel_views.esm";

class Partner extends models.Model {
    _name = "partner";

    name = fields.Char();
    category = fields.Char();

    _records = [
        {id: 1, name: "Alpha", category: "A"},
        {id: 2, name: "Beta", category: "A"},
        {id: 3, name: "Gamma", category: "B"},
    ];

    _views = {
        form: `<form><field name="name"/></form>`,
    };
}

defineModels({...webModels, Partner});

const LIST_ARCH = `<list js_class="side_panel_list"><field name="name"/></list>`;
const KANBAN_ARCH = `
    <kanban js_class="side_panel_kanban">
        <templates>
            <t t-name="card"><field name="name"/></t>
        </templates>
    </kanban>`;

describe.current.tags("desktop");

async function checkPanel(selectFirst) {
    expect(".o_side_panel").toHaveCount(0);

    await selectFirst();
    await waitFor(".o_side_panel");
    expect(".o_side_panel_position").toHaveText("1 / 3");
    expect(".o_side_panel_selected").toHaveCount(1);
    await waitFor(".o_side_panel .o_field_widget[name='name']");
    expect(".o_side_panel .o_field_widget[name='name']").toHaveText("Alpha");

    await click(".o_side_panel_next");
    await waitFor(".o_side_panel_position:contains('2 / 3')");
    await waitFor(".o_side_panel .o_field_widget[name='name']:contains('Beta')");

    await click(".o_side_panel_prev");
    await click(".o_side_panel_prev");
    await waitFor(".o_side_panel_position:contains('3 / 3')");

    await click(".o_side_panel_close");
    await waitForNone(".o_side_panel");
    expect(".o_side_panel_selected").toHaveCount(0);
}

test("a click on a list row shows the record in the panel", async () => {
    await mountView({type: "list", resModel: "partner", arch: LIST_ARCH});
    await checkPanel(() => click(".o_data_row:first .o_data_cell:first"));
});

test("a click on a kanban card shows the record in the panel", async () => {
    await mountView({type: "kanban", resModel: "partner", arch: KANBAN_ARCH});
    await checkPanel(() => click(".o_kanban_record:first"));
});

test("the panel stays off when the context disables it", async () => {
    await mountView({
        type: "list",
        resModel: "partner",
        arch: LIST_ARCH,
        context: {disable_side_panel: true},
    });
    await click(".o_data_row:first .o_data_cell:first");
    expect(".o_side_panel").toHaveCount(0);
});

test("on a small screen a click opens the form as usual", async () => {
    await resize({width: 900, height: 800});
    await mountView({
        type: "list",
        resModel: "partner",
        arch: LIST_ARCH,
        selectRecord: (resId) => expect.step(`open ${resId}`),
    });
    await click(".o_data_row:first .o_data_cell:first");
    expect(".o_side_panel").toHaveCount(0);
    expect.verifySteps(["open 1"]);
});

test("the panel opens in a list grouped on two levels", async () => {
    await mountView({
        type: "list",
        resModel: "partner",
        arch: LIST_ARCH,
        groupBy: ["category", "name"],
    });
    await click(".o_group_header:first");
    await waitFor(".o_group_header:contains('Alpha')");
    await click(".o_group_header:contains('Alpha')");
    await waitFor(".o_data_row");
    await click(".o_data_row:first .o_data_cell:first");
    await waitFor(".o_side_panel");
    expect(".o_side_panel_position").toHaveText("1 / 1");
});
