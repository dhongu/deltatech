/** @odoo-module **/
import {describe, expect, test} from "@odoo/hoot";
import {click, dblclick, drag, keyDown, press, queryOne, resize, waitFor, waitForNone} from "@odoo/hoot-dom";
import {animationFrame} from "@odoo/hoot-mock";
import {defineModels, fields, models, mountView, onRpc, webModels} from "@web/../tests/web_test_helpers";
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

test("refresh reads the record of the panel again", async () => {
    onRpc("partner", "web_read", () => expect.step("web_read"));
    await mountView({type: "list", resModel: "partner", arch: LIST_ARCH});
    await click(".o_data_row:first .o_data_cell:first");
    await waitFor(".o_side_panel .o_field_widget[name='name']");
    expect.verifySteps(["web_read"]);

    await click(".o_side_panel_refresh");
    await animationFrame();
    await waitFor(".o_side_panel .o_field_widget[name='name']");
    expect.verifySteps(["web_read"]);
});

const WIDTH_KEY = "deltatech_web_side_panel.width";

async function openPanel() {
    localStorage.removeItem(WIDTH_KEY);
    await mountView({type: "list", resModel: "partner", arch: LIST_ARCH});
    await click(".o_data_row:first .o_data_cell:first");
    await waitFor(".o_side_panel .o_field_widget[name='name']");
    await animationFrame();
}

const panelWidth = () => Math.round(queryOne(".o_side_panel").getBoundingClientRect().width);

test("the panel has an accessible resize handle", async () => {
    await openPanel();
    expect(".o_side_panel_resizer").toHaveCount(1);
    expect(".o_side_panel_resizer").toHaveAttribute("role", "separator");
    expect(".o_side_panel_resizer").toHaveAttribute("aria-orientation", "vertical");
    expect(".o_side_panel_resizer").toHaveAttribute("tabindex", "0");
    expect(".o_side_panel_resizer").toHaveAttribute("aria-valuemin", "300");
    expect(parseInt(queryOne(".o_side_panel_resizer").getAttribute("aria-valuenow"), 10)).toBeGreaterThan(299);
});

test("dragging the handle changes the width, within the limits", async () => {
    await openPanel();
    const start = panelWidth();
    const rightEdge = queryOne(".o_side_panel").getBoundingClientRect().right;
    const {moveTo, drop} = await drag(".o_side_panel_resizer");
    await moveTo(".o_side_panel_resizer", {position: {x: rightEdge - 420, y: 100}, relative: false});
    await drop();
    await animationFrame();
    expect(panelWidth()).not.toBe(start);
    expect(panelWidth()).toBeGreaterThan(299);
    const max = Math.floor(queryOne(".o_side_panel").parentElement.clientWidth * 0.7);
    expect(panelWidth()).not.toBeGreaterThan(max + 1);
});

test("the keyboard resizes the panel and stops at the limits", async () => {
    await openPanel();
    queryOne(".o_side_panel_resizer").focus();
    await keyDown("Home");
    await animationFrame();
    expect(panelWidth()).toBe(300);
    await press("ArrowLeft");
    await animationFrame();
    expect(panelWidth()).toBe(320);
    await press("ArrowRight");
    await press("ArrowRight");
    await press("ArrowRight");
    await animationFrame();
    expect(panelWidth()).toBe(300);
    await press("End");
    await animationFrame();
    const max = Math.floor(queryOne(".o_side_panel").parentElement.clientWidth * 0.7);
    expect(panelWidth()).not.toBeGreaterThan(max + 1);
    expect(panelWidth()).toBeGreaterThan(320);
});

test("a double click on the handle restores the default width", async () => {
    await openPanel();
    queryOne(".o_side_panel_resizer").focus();
    await press("Home");
    await animationFrame();
    expect(panelWidth()).toBe(300);
    await dblclick(".o_side_panel_resizer");
    await animationFrame();
    const container = queryOne(".o_side_panel").parentElement.clientWidth;
    expect(panelWidth()).toBe(Math.round(Math.min(480, Math.max(340, container * 0.34))));
    expect(localStorage.getItem(WIDTH_KEY)).toBe(null);
});

test("the chosen width is kept and applied when the panel opens again", async () => {
    await openPanel();
    queryOne(".o_side_panel_resizer").focus();
    await press("Home");
    await press("ArrowLeft");
    await animationFrame();
    expect(localStorage.getItem(WIDTH_KEY)).toBe("320");

    await click(".o_side_panel_close");
    await waitForNone(".o_side_panel");
    await click(".o_data_row:first .o_data_cell:first");
    await waitFor(".o_side_panel");
    await animationFrame();
    expect(panelWidth()).toBe(320);
});

test("a double click on a row opens the full form, a click only selects", async () => {
    await mountView({
        type: "list",
        resModel: "partner",
        arch: LIST_ARCH,
        selectRecord: (resId) => expect.step(`open ${resId}`),
    });
    await click(".o_data_row:eq(1) .o_data_cell:first");
    await waitFor(".o_side_panel");
    expect.verifySteps([]);

    await dblclick(".o_data_row:first .o_data_cell:first");
    expect.verifySteps(["open 1"]);
});

test("a double click on a kanban card opens the full form", async () => {
    await mountView({
        type: "kanban",
        resModel: "partner",
        arch: KANBAN_ARCH,
        selectRecord: (resId) => expect.step(`open ${resId}`),
    });
    await dblclick(".o_kanban_record:first");
    expect.verifySteps(["open 1"]);
});
