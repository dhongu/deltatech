/**
 * Tour: verifies city change populates ZIP and toggles city inputs on portal address form.
 */
import {registry} from "@web/core/registry";

registry.category("web_tour.tours").add("deltatech_website_city_tour_city_zip", {
    url: "/my/account",
    steps: () => [
        {
            content: "Wait until country select is available",
            trigger: 'select[name="country_id"]',
        },
        {
            // Folosim selectByLabel nativ (Hoot) ca să garantăm că Interaction
            // a apucat să atașeze handler-ele și că evenimentul change e procesat.
            content: "Select test country by label",
            trigger: 'select[name="country_id"]',
            // Created by the test: country name is "Testland"
            run: "selectByLabel Testland",
        },
        {
            // OnChangeCountry e debounced 500ms + RPC /my/address/country_info/{id};
            // așteaptă explicit ca opțiunile state-ului să fie populate.
            content: "Wait until states are populated for the selected country",
            trigger: '#div_state select[name="state_id"] option[value]:not([value=""])',
        },
        {
            content: "Select test state by label (triggers city RPC)",
            trigger: 'select[name="state_id"]',
            // Created by the test: state name is "Test State"
            run: "selectByLabel Test State",
        },
        {
            content: "Wait until cities are populated",
            trigger: 'select[name="city_id"] option[value]:not([value=""])',
        },
        {
            content: "Pick city with ZIP and check ZIP filled",
            trigger: 'select[name="city_id"]',
            // City created with ZIP: "Alpha City"
            run: "selectByLabel Alpha City",
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
