import {describe, expect, test} from "@odoo/hoot";
import {queryOne} from "@odoo/hoot-dom";
import {clickSave, contains, defineModels, fields, models, mountView, onRpc} from "@web/../tests/web_test_helpers";

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
        expect(".o_field_many2one_badge .o_delete").toHaveCount(0);
    });

    test("Many2oneBadgeField: edit mode removes and replaces the value", async () => {
        onRpc("task", "web_save", ({args}) => {
            expect.step(`web_save ${JSON.stringify(args[1])}`);
        });
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

        // Editabil: badge cu buton de ștergere, fără câmp de căutare
        expect(".o_field_many2one_badge .badge.o_tag").toHaveText("Partner 1");
        expect(".o_field_many2one_badge .o_delete").toHaveCount(1);
        expect(".o_field_many2one_badge input").toHaveCount(0);

        // Ștergerea valorii scoate badge-ul și afișează căutarea
        // (butonul e ascuns prin CSS până la hover)
        await contains(".o_field_many2one_badge .o_delete", {visible: false}).click();
        expect(".o_field_many2one_badge .badge.o_tag").toHaveCount(0);
        expect(".o_field_many2one_badge input").toHaveCount(1);

        // Alegerea altui partener din autocomplete reface badge-ul cu culoarea lui
        await contains(".o_field_many2one_badge input").edit("Partner 2", {confirm: false});
        await contains(".o_field_many2one_badge .o-autocomplete--dropdown-item:first").click();
        expect(".o_field_many2one_badge .badge.o_tag").toHaveText("Partner 2");
        expect(".o_field_many2one_badge .badge.o_tag").toHaveClass("o_tag_color_2");

        await clickSave();
        expect.verifySteps(['web_save {"partner_id":2}']);
    });

    test("Many2oneBadgeField: clicking the badge changes the partner color", async () => {
        onRpc("partner", "write", ({args}) => {
            expect.step(`write ${JSON.stringify(args)}`);
        });
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

        await contains(".o_field_many2one_badge .badge.o_tag").click();
        expect(".o_tag_popover .o_colorlist button").toHaveCount(11);

        await contains(".o_tag_popover .o_colorlist_item_color_5").click();
        expect.verifySteps(['write [[1],{"color":5}]']);
        expect(".o_tag_popover").toHaveCount(0);
        expect(".o_field_many2one_badge .badge.o_tag").toHaveClass("o_tag_color_5");
    });
});
