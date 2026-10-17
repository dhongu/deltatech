import {defineWebsiteModels, setupWebsiteBuilder} from "@website/../tests/builder/website_helpers";

import {describe, expect, test} from "@odoo/hoot";
import {queryAll} from "@odoo/hoot-dom";
import {contains} from "@web/../tests/web_test_helpers";

defineWebsiteModels();

describe.current.tags("desktop");

const searchbarHTML = (typing = "") => `
    <form method="get" data-snippet="s_searchbar_input" class="o_searchbar_form s_searchbar_input" action="/website/search" data-name="Search">
        <div role="search" class="input-group">
            <input type="search" name="search" class="search-query form-control oe_search_box" placeholder="Search..." data-limit="5" data-order-by="name asc" data-search-type="all"/>
            <button type="submit" aria-label="Search" title="Search" class="btn oe_search_button btn-primary">
                <i class="oi oi-search" contenteditable="false"></i>
            </button>
        </div>
        <input name="order" type="hidden" class="o_search_order_by" value="name asc"/>
        ${typing}
    </form>
`;

const TYPING = `
    <ul class="o_searchbar_typing d-none" aria-hidden="true">
        <li class="o_searchbar_typing_prefix">e.g.</li>
        <li>e-Invoice</li>
        <li>credit note</li>
    </ul>
`;

const toggle = "[data-label='Typing examples'] input[type=checkbox]";
const prefixInput = "[data-label='Prefix'] input";
const exampleInputs = ".we-bg-options-container input[name=value]";

function examples() {
    // The list is hidden: its text is read from textContent, not innerText.
    return queryAll(":iframe .o_searchbar_typing > li:not(.o_searchbar_typing_prefix)").map((el) => el.textContent);
}

function prefix() {
    return queryAll(":iframe .o_searchbar_typing > li.o_searchbar_typing_prefix").map((el) => el.textContent)[0];
}

test("searchbar typing option: turning it on writes the hidden list, off removes it", async () => {
    await setupWebsiteBuilder(searchbarHTML());
    await contains(":iframe .search-query").click();
    expect(toggle).not.toBeChecked();
    expect(prefixInput).toHaveCount(0);

    await contains(toggle).click();
    expect(":iframe .o_searchbar_form > ul.o_searchbar_typing.d-none").toHaveAttribute("aria-hidden", "true");
    expect(prefix()).toBe("e.g.");
    expect(examples()).toEqual(["Example"]);
    expect(prefixInput).toHaveValue("e.g.");
    expect(exampleInputs).toHaveCount(1);

    await contains(toggle).click();
    expect(":iframe .o_searchbar_typing").toHaveCount(0);
});

test("searchbar typing option: reads the existing examples and edits them", async () => {
    await setupWebsiteBuilder(searchbarHTML(TYPING));
    await contains(":iframe .search-query").click();
    expect(toggle).toBeChecked();
    expect(prefixInput).toHaveValue("e.g.");
    expect(exampleInputs).toHaveCount(2);

    await contains(`${exampleInputs}:eq(1)`).edit("bank statement");
    expect(examples()).toEqual(["e-Invoice", "bank statement"]);

    await contains(".we-bg-options-container .builder_list_add_item").click();
    expect(examples()).toEqual(["e-Invoice", "bank statement", "Example"]);

    await contains(".we-bg-options-container .builder_list_remove_item:first").click();
    expect(examples()).toEqual(["bank statement", "Example"]);
    expect(":iframe .o_searchbar_typing > li:first").toHaveClass("o_searchbar_typing_prefix");
});

test("searchbar typing option: an empty prefix removes it, a new one is put first", async () => {
    await setupWebsiteBuilder(searchbarHTML(TYPING));
    await contains(":iframe .search-query").click();

    await contains(prefixInput).edit("");
    expect(":iframe .o_searchbar_typing_prefix").toHaveCount(0);
    expect(examples()).toEqual(["e-Invoice", "credit note"]);

    await contains(prefixInput).edit("try");
    expect(":iframe .o_searchbar_typing > li:first").toHaveClass("o_searchbar_typing_prefix");
    expect(prefix()).toBe("try");
});
