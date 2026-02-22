/**
 * Tour: verifies city change populates ZIP and toggles city inputs on portal address form.
 */
import {registry} from "@web/core/registry";

function setSelectByLabel(selector, labelText, partial = false) {
    const select = document.querySelector(selector);
    if (!select) return false;
    const option = Array.from(select.options).find((o) => {
        const text = o.text.trim();
        return partial ? text.includes(labelText) : text === labelText;
    });
    if (!option) {
        return false;
    }
    select.value = option.value;
    select.dispatchEvent(new Event("change", {bubbles: true}));
    // Also trigger 'input' as some modern listeners use it
    select.dispatchEvent(new Event("input", {bubbles: true}));
    return true;
}

registry.category("web_tour.tours").add("deltatech_website_city_tour_city_zip", {
    url: "/my/account",
    steps: () => [
        {
            content: "Wait until country select is available",
            trigger: 'select[name="country_id"]',
        },
        {
            content: "Check if cities are pre-populated (if partner had state)",
            trigger: 'select[name="city_id"]:not(:visible)',
        },
        {
            content: "Select test country by label",
            trigger: 'select[name="country_id"]',
            run() {
                // Created by the test: country name is "Testland"
                setSelectByLabel('select[name="country_id"]', "Testland");
            },
        },
        {
            content: "Wait for state field to be visible",
            trigger: '#div_state select[name="state_id"]',
        },
        {
            content: "Select test state by label (triggers city RPC)",
            trigger: 'select[name="state_id"]',
            run() {
                // Created by the test: state name is "Test State"
                setSelectByLabel('select[name="state_id"]', "Test State");
            },
        },
        {
            content: "Wait until cities are populated",
            trigger: 'select[name="city_id"] option:not([value=""]):not(:visible)',
        },
        {
            content: "Check if city text field is hidden",
            trigger: "#div_city:not(:visible)",
        },
        {
            content: "Pick city with ZIP and check ZIP filled",
            trigger: 'select[name="city_id"]',
            run() {
                // City created with ZIP: "Alpha City". Label may include ZIP: "Alpha City (12345)"
                setSelectByLabel('select[name="city_id"]', "Alpha City", true);
            },
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
    ],
});

registry.category("web_tour.tours").add("deltatech_website_city_tour_portal_save", {
    url: "/my/account",
    steps: () => [
        {
            content: "Wait until city select is available",
            trigger: 'select[name="city_id"]',
        },
        {
            content: "Pick Alpha City",
            trigger: 'select[name="city_id"]',
            run() {
                // Label may include ZIP: "Alpha City (12345)"
                setSelectByLabel('select[name="city_id"]', "Alpha City", true);
            },
        },
        {
            content: "Save the form",
            trigger: 'button:contains("Save")',
            run: "click",
        },
        {
            content: "Wait for the portal home page",
            trigger: ".o_portal_my_home",
        },
    ],
});
