import {after, expect, test} from "@odoo/hoot";
import {queryOne} from "@odoo/hoot-dom";
import {defineModels, fields, models, mountView} from "@web/../tests/web_test_helpers";

const UNSAFE =
    "# Title\n\n**bold** text\n\n" +
    '<img src="x" onerror="window.__md_probe = true">\n\n' +
    "<script>window.__md_probe = true;</script>\n\n" +
    "[link](javascript:window.__md_probe=true)";

class Note extends models.Model {
    _name = "md.note";
    body = fields.Text();
    _records = [{id: 1, body: UNSAFE}];
}

defineModels([Note]);

for (const readonly of [false, true]) {
    test(`stored HTML is sanitized before display (readonly=${readonly})`, async () => {
        after(() => delete window.__md_probe);
        await mountView({
            type: "form",
            resModel: "md.note",
            resId: 1,
            arch: `<form><field name="body" widget="markdown" readonly="${readonly}"/></form>`,
        });
        const editor = queryOne(".o_md_editor");
        // Markdown is still rendered
        expect(editor.querySelector("h1")).toHaveText("Title");
        expect(editor.querySelector("strong")).toHaveText("bold");
        // Nothing executable reaches the DOM
        expect(editor.querySelectorAll("script")).toHaveLength(0);
        const attrs = [...editor.querySelectorAll("*")].flatMap((el) => [...el.attributes]);
        expect(attrs.filter((a) => a.name.startsWith("on"))).toEqual([]);
        expect(attrs.filter((a) => /javascript:/i.test(a.value))).toEqual([]);
        expect(window.__md_probe).toBe(undefined);
    });
}
