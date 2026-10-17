import {setupInteractionWhiteList, startInteractions} from "@web/../tests/public/helpers";

import {advanceTime, describe, expect, mockMatchMedia, test} from "@odoo/hoot";
import {queryOne} from "@odoo/hoot-dom";
import {patchWithCleanup} from "@web/../tests/web_test_helpers";

setupInteractionWhiteList("deltatech_website_searchbar_typing.searchbar_typing");

describe.current.tags("interaction_dev");

const FORM = `
    <form class="o_searchbar_form" action="/search">
        <input type="search" name="search" class="search-query" placeholder="Search the guides"/>
        <ul class="o_searchbar_typing d-none" aria-hidden="true">
            <li class="o_searchbar_typing_prefix">e.g.</li>
            <li>abc</li>
            <li>de</li>
        </ul>
    </form>
`;

// The box is always in view, unless a test says otherwise.
let observerCallback = null;
class FakeIntersectionObserver {
    constructor(callback) {
        observerCallback = callback;
    }
    observe() {
        observerCallback([{isIntersecting: true}]);
    }
    disconnect() {
        observerCallback = null;
    }
}

function setup() {
    patchWithCleanup(window, {IntersectionObserver: FakeIntersectionObserver});
    mockMatchMedia({"prefers-reduced-motion": "no-preference"});
}

function placeholder() {
    return queryOne("input").getAttribute("placeholder");
}

test("searchbar typing: types, holds, erases and goes to the next example", async () => {
    setup();
    const {core} = await startInteractions(FORM);
    expect(core.interactions).toHaveLength(1);
    expect(placeholder()).toBe("Search the guides");
    await advanceTime(1500);
    expect(placeholder()).toBe("e.g. a");
    await advanceTime(140);
    expect(placeholder()).toBe("e.g. abc");
    await advanceTime(1800);
    expect(placeholder()).toBe("e.g. ab");
    await advanceTime(60);
    expect(placeholder()).toBe("e.g. ");
    await advanceTime(400);
    expect(placeholder()).toBe("e.g. d");
});

test("searchbar typing: focus stops it for good and restores the placeholder", async () => {
    setup();
    await startInteractions(FORM);
    await advanceTime(1600);
    expect(placeholder()).toBe("e.g. ab");
    queryOne("input").dispatchEvent(new FocusEvent("focus"));
    expect(placeholder()).toBe("Search the guides");
    queryOne("input").dispatchEvent(new FocusEvent("blur"));
    await advanceTime(10000);
    expect(placeholder()).toBe("Search the guides");
});

test("searchbar typing: does not run with prefers-reduced-motion", async () => {
    patchWithCleanup(window, {IntersectionObserver: FakeIntersectionObserver});
    mockMatchMedia({"prefers-reduced-motion": "reduce"});
    await startInteractions(FORM);
    await advanceTime(5000);
    expect(placeholder()).toBe("Search the guides");
});

test("searchbar typing: stops when reduced motion is turned on, waits out of view", async () => {
    setup();
    await startInteractions(FORM);
    await advanceTime(1500);
    expect(placeholder()).toBe("e.g. a");
    observerCallback([{isIntersecting: false}]);
    expect(placeholder()).toBe("Search the guides");
    await advanceTime(5000);
    expect(placeholder()).toBe("Search the guides");
    observerCallback([{isIntersecting: true}]);
    await advanceTime(1500);
    expect(placeholder()).toBe("e.g. a");
    mockMatchMedia({"prefers-reduced-motion": "reduce"});
    expect(placeholder()).toBe("Search the guides");
});

test("searchbar typing: the box keeps a stable accessible name", async () => {
    setup();
    const {core} = await startInteractions(FORM);
    expect(queryOne("input")).toHaveAttribute("aria-label", "Search the guides");
    core.stopInteractions();
    expect(queryOne("input")).not.toHaveAttribute("aria-label");
    expect(placeholder()).toBe("Search the guides");
});

test("searchbar typing: search forms without examples are left alone", async () => {
    setup();
    const {core} = await startInteractions(`
        <form class="o_searchbar_form" action="/search">
            <input type="search" name="search" class="search-query" placeholder="Search..."/>
        </form>
    `);
    expect(core.interactions).toHaveLength(0);
});
