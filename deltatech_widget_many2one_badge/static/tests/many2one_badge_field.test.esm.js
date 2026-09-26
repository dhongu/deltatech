/** @odoo-module **/

import {describe, expect, test} from "@odoo/hoot";
import {queryOne} from "@odoo/hoot-dom";
import {defineModels, fields, models, mountView} from "@web/../tests/web_test_helpers";

describe("Many2oneBadgeField", () => {
    class Partner extends models.Model {
        name = fields.Char({string: "Name"});
        color = fields.Integer({string: "Color"});

        _records = [
            {id: 1, name: "Partner 1", color: 1},
            {id: 2, name: "Partner 2", color: 2},
        ];
    }

    class Task extends models.Model {
        name = fields.Char({string: "Task Name"});
        partner_id = fields.Many2one({relation: "partner", string: "Partner"});

        _records = [{id: 1, name: "Task 1", partner_id: 1}];
    }

    defineModels([Partner, Task]);

    test("Many2oneBadgeField: readonly rendering", async () => {
        await mountView({
            type: "form",
            resModel: "task",
            resId: 1,
            arch: `
                <form>
                    <field name="partner_id" widget="many2one_badge" readonly="1" options="{'color_field': 'color'}"/>
                </form>
            `,
        });

        const badge = queryOne(".badge.o_tag");
        expect(badge).toBeDisplayed();
        expect(badge).toHaveText("Partner 1");
        expect(badge).toHaveClass("o_tag_color_1");
    });

    test("Many2oneBadgeField: edit mode rendering", async () => {
        await mountView({
            type: "form",
            resModel: "task",
            resId: 1,
            arch: `
                <form>
                    <field name="partner_id" widget="many2one_badge" options="{'color_field': 'color'}"/>
                </form>
            `,
        });

        const badge = queryOne(".badge.o_tag");
        expect(badge).toBeDisplayed();
        expect(badge).toHaveText("Partner 1");
        // În modul edit (sau readonly fără permisiuni de editare în test), badge-ul ar trebui să fie vizibil.
    });
});
