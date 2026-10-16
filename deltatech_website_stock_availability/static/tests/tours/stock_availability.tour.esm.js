/**
 * Tour: verifies stock availability message on product page.
 */
import {registry} from "@web/core/registry";

registry.category("web_tour.tours").add("deltatech_website_stock_availability_tour", {
    url: "/shop",
    steps: () => [
        {
            content: "Search for Test Product A",
            trigger: 'form input[name="search"]',
            run: "edit Test Product A",
        },
        {
            content: "Click on Search button",
            trigger: 'form:has(input[name="search"]) .oe_search_button',
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "Click on Test Product A",
            trigger: '.oe_product_cart a:contains("Test Product A")',
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "Check if 'In stock' message is visible",
            trigger: '.lead_time_messages:contains("In stock")',
        },
        {
            content: "Go back to shop",
            trigger: 'a:contains("Shop")',
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "Search for Test Product C",
            trigger: 'form input[name="search"]',
            run: "edit Test Product C",
        },
        {
            content: "Click on Search button",
            trigger: 'form:has(input[name="search"]) .oe_search_button',
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "Click on Test Product C",
            trigger: '.oe_product_cart a:contains("Test Product C")',
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "Check if 'In stock at vendor' message is visible for product without stock",
            trigger: '.lead_time_messages:contains("In stock at vendor")',
        },
    ],
});
