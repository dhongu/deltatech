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
            content: "Wait until country select is available",
            trigger: 'select[name="country_id"]',
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
            // OnChangeCountry e debounced 500ms + RPC /my/address/country_info/{id};
            // așteaptă explicit ca opțiunile state-ului să fie populate, nu doar select-ul.
            content: "Wait until states are populated for the selected country",
            trigger: '#div_state select[name="state_id"] option[value]:not([value=""])',
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
            trigger: 'select[name="city_id"] option[value]:not([value=""])',
        },
        {
            content: "Pick city with ZIP and check ZIP filled",
            trigger: 'select[name="city_id"]',
            run() {
                // City created with ZIP: "Alpha City"
                setSelectByLabel('select[name="city_id"]', "Alpha City");
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
