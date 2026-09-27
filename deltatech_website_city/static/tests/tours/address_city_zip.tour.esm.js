/**
 * Tour: verifies city change populates ZIP and toggles city inputs on portal address form.
 */
import {registry} from "@web/core/registry";

function setSelectByLabel(selector, labelText) {
    const select = document.querySelector(selector);
    if (!select) return false;
    const option = Array.from(select.options).find((o) => o.text.trim() === labelText);
    if (!option) return false;
    select.value = option.value;
    select.dispatchEvent(new Event("change", {bubbles: true}));
    return true;
}

registry.category("web_tour.tours").add("deltatech_website_city_tour_city_zip", {
    url: "/my/account",
    steps: () => [
        {
            content: "Wait until the test country is offered",
            trigger: 'select[name="country_id"]:has(option:contains("Testland"))',
            run() {
                // Created by the test: country name is "Testland"
                setSelectByLabel('select[name="country_id"]', "Testland");
            },
        },
        {
            content: "Wait for the states of the country (loaded after the country change)",
            trigger: '#div_state select[name="state_id"]:has(option:contains("Test State"))',
            run() {
                // Created by the test: state name is "Test State"
                setSelectByLabel('select[name="state_id"]', "Test State");
            },
        },
        {
            content: "Wait until cities are populated, then pick the city with a ZIP",
            trigger: '#div_city_id select[name="city_id"]:has(option:contains("Alpha City"))',
            run() {
                // City created with ZIP: "Alpha City"
                setSelectByLabel('select[name="city_id"]', "Alpha City");
            },
        },
        {
            content: "The ZIP is filled from the city",
            trigger: 'input[name="zip"]:value(12345)',
        },
        {
            content: "The free-text city stays hidden",
            trigger: "#div_city:not(:visible)",
        },
        {
            content: "Switch back to placeholder city (empty) to allow manual ZIP entry",
            trigger: 'select[name="city_id"]',
            run() {
                const select = document.querySelector('select[name="city_id"]');
                select.value = "";
                select.dispatchEvent(new Event("change", {bubbles: true}));
            },
        },
        {
            content: "The ZIP is cleared",
            trigger: 'input[name="zip"]:not(:value(12345))',
        },
    ],
});
