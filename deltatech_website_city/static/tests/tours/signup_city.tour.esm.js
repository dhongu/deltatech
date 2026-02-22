/** @odoo-module **/

import {registry} from "@web/core/registry";

registry.category("web_tour.tours").add("deltatech_website_city_signup_tour", {
    url: "/web/signup",
    steps: () => [
        {
            content: "Fill Email",
            trigger: 'input[name="login"]',
            run: "edit new_user@test.com",
        },
        {
            content: "Fill Name",
            trigger: 'input[name="name"]',
            run: "edit New Test User",
        },
        {
            content: "Fill Password",
            trigger: 'input[name="password"]',
            run: "edit password123",
        },
        {
            content: "Confirm Password",
            trigger: 'input[name="confirm_password"]',
            run: "edit password123",
        },
        {
            content: "Submit Signup",
            trigger: 'button[type="submit"]',
            run: "click",
        },
        {
            content: "Verify we are on the portal page",
            trigger: ".o_portal_my_home",
        },
        {
            content: "Navigate to details to check if fields are present",
            trigger: 'a[href="/my/account"]',
            run: "click",
        },
        {
            content: "Check if city_id field is present",
            trigger: 'select[name="city_id"]:not(:visible)',
        },
    ],
});
