import {after, expect, test} from "@odoo/hoot";
import {queryOne} from "@odoo/hoot-dom";
import {clickSave, contains, defineModels, fields, models, mountView, onRpc} from "@web/../tests/web_test_helpers";
import {MarkdownField, createTurndownService} from "@deltatech_markdown_field/fields/markdown_field.esm";

const UNSAFE =
    "# Title\n\n**bold** text\n\n" +
    '<img src="x" onerror="window.__md_probe = true">\n\n' +
    "<script>window.__md_probe = true;</script>\n\n" +
    "[link](javascript:window.__md_probe=true)";

// Strikethrough, a GFM table (alignment, escaped pipe) and a task list, in the
// form turndown writes them back, so a lossless round trip leaves them unchanged.
const GFM =
    "Text ~~tăiat~~ aici\n\n" +
    "| Produs | Cant. |\n| --- | ---: |\n| Palet A \\| B | 2 |\n\n" +
    "-   [x] gata\n-   [ ] de făcut";

function roundTrip(md) {
    const html = MarkdownField.prototype._mdToHtml(md);
    return createTurndownService().turndown(html).trim();
}

class Note extends models.Model {
    _name = "md.note";
    name = fields.Char();
    body = fields.Text();
    _records = [
        {id: 1, name: "unsafe", body: UNSAFE},
        {id: 2, name: "gfm", body: GFM},
    ];
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

test("strikethrough, tables and task lists survive the Markdown round trip", () => {
    expect(roundTrip(GFM)).toBe(GFM);
});

test("strikethrough from the toolbar is written as Markdown", () => {
    const md = createTurndownService().turndown("<p>a <strike>b</strike> <s>c</s> <del>d</del></p>");
    expect(md).toBe("a ~~b~~ ~~c~~ ~~d~~");
});

test("a table GFM cannot express is kept as HTML", () => {
    const md = createTurndownService().turndown(
        '<table><tbody><tr><td colspan="2">Total</td></tr><tr><td>1</td><td>2</td></tr></tbody></table>'
    );
    expect(md).toInclude("<table>");
    expect(md).toInclude("colspan");
    expect(roundTrip(md)).toBe(md);
});

test("focus and blur in the editor do not rewrite GFM content", async () => {
    let savedValues = null;
    onRpc("web_save", ({args}) => {
        savedValues = args[1];
    });
    await mountView({
        type: "form",
        resModel: "md.note",
        resId: 2,
        arch: `<form><field name="name"/><field name="body" widget="markdown"/></form>`,
    });
    const editor = queryOne(".o_md_editor");
    editor.focus();
    editor.blur();
    await contains(".o_field_widget[name=name] input").edit("gfm edited");
    await clickSave();
    expect(savedValues).toEqual({name: "gfm edited"});
});
