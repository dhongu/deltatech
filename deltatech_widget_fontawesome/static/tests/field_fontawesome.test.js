import {describe, expect, test} from "@odoo/hoot";
import {defineModels, defineWebModels, fields, models, mountView} from "@web/../tests/web_test_helpers";

describe("deltatech_widget_fontawesome", () => {
    class Category extends models.Model {
        name = fields.Char({string: "Name"});
        icon = fields.Char({string: "Icon"});

        _records = [
            {id: 1, name: "Call", icon: "fa-phone"},
            {id: 2, name: "Visit", icon: false},
        ];
    }

    defineWebModels();
    defineModels([Category]);

    const formArch = `<form><field name="name"/><field name="icon" widget="fontawesome"/></form>`;

    test("shows the icon and the class name as tooltip", async () => {
        await mountView({type: "form", resModel: "category", resId: 1, arch: formArch});

        expect(".o_field_widget[name=icon] i").toHaveClass(["fa", "fa-phone"]);
        expect(".o_field_widget[name=icon] i").toHaveAttribute("data-tooltip", "Fa-phone");
    });

    test("an unset field renders empty, without error (#3511)", async () => {
        await mountView({type: "form", resModel: "category", resId: 2, arch: formArch});

        expect(".o_field_widget[name=icon] i").toHaveCount(1);
        expect(".o_field_widget[name=icon] i").not.toHaveClass("fa");
        expect(".o_field_widget[name=icon] i").not.toHaveAttribute("data-tooltip", "Fa-phone");
        expect(".o_field_widget[name=icon] i").not.toHaveAttribute("class", "fa false");
    });

    test("a new record opens without error", async () => {
        await mountView({type: "form", resModel: "category", arch: formArch});

        expect(".o_field_widget[name=icon] i").toHaveCount(1);
        expect(".o_field_widget[name=icon] i").not.toHaveClass("fa");
    });

    test("list: icon on filled rows, empty cell on unset rows", async () => {
        await mountView({
            type: "list",
            resModel: "category",
            arch: `<list><field name="name"/><field name="icon" widget="fontawesome"/></list>`,
        });

        expect(".o_data_row .o_field_widget[name=icon] i.fa").toHaveCount(1);
        expect(".o_data_row:eq(1) .o_field_widget[name=icon] i").not.toHaveClass("fa");
    });
});
