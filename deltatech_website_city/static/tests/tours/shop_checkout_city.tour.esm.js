/** @odoo-module **/

import * as tourUtils from "@website_sale/js/tours/tour_utils";
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
    select.dispatchEvent(new Event("input", {bubbles: true}));
    return true;
}

registry.category("web_tour.tours").add("deltatech_website_city_shop_checkout_tour", {
    url: "/shop",
    steps: () => [
        ...tourUtils.searchProduct("Test Product", {select: true}),
        {
            content: "click on add to cart",
            trigger: '#product_detail form[action^="/shop/cart/update"] #add_to_cart',
            run: "click",
        },
        tourUtils.goToCart(),
        {
            content: "Go to address page directly",
            trigger: 'a[href^="/shop/checkout"]',
            run() {
                window.location.href = "/shop/address";
            },
        },
        {
            content: "Wait for address form (any select with id city_id or name country_id)",
            trigger: '#city_id, select[name="country_id"]',
        },
        {
            content: "Check if city_id field is present in billing address",
            trigger: "#city_id:not(:visible)",
        },
        {
            content: "Select country Testland",
            trigger: 'select[name="country_id"]',
            run() {
                setSelectByLabel('select[name="country_id"]', "Testland");
            },
        },
        {
            content: "Select state Test State",
            trigger: 'select[name="state_id"]',
            run() {
                setSelectByLabel('select[name="state_id"]', "Test State");
            },
        },
        {
            content: "Wait until cities are populated and visible",
            trigger: '#city_id:visible option:not([value=""])',
        },
        {
            content: "Pick Alpha City",
            trigger: "#city_id",
            run() {
                setSelectByLabel("#city_id", "Alpha City", true);
            },
        },
        {
            content: "Fill mandatory fields",
            trigger: 'input[name="name"]',
            run() {
                document.querySelector('input[name="name"]').value = "Test User";
                document.querySelector('input[name="email"]').value = "test@test.com";
                document.querySelector('input[name="phone"]').value = "123456789";
                document.querySelector('input[name="street"]').value = "Test Street";
            },
        },
        {
            content: "Confirm billing address",
            trigger: '.oe_cart button[type="submit"]',
            run: "click",
        },
        {
            content: "Check if we are on confirm order page",
            trigger: 'a[href^="/shop/confirm_order"]',
        },
        {
            content: "Go to edit address to add a delivery address",
            trigger: 'a[href^="/shop/checkout?edit_address=1"]',
            run: "click",
        },
        {
            content: "Click to add a new address (delivery)",
            trigger: 'a[href^="/shop/address?address_type=delivery"]',
            run: "click",
        },
        {
            content: "Check if city_id field is present in delivery address form",
            trigger: "#city_id:not(:visible)",
        },
        {
            content: "Select country Testland for delivery",
            trigger: 'select[name="country_id"]',
            run() {
                setSelectByLabel('select[name="country_id"]', "Testland");
            },
        },
        {
            content: "Select state Test State for delivery",
            trigger: 'select[name="state_id"]',
            run() {
                setSelectByLabel('select[name="state_id"]', "Test State");
            },
        },
        {
            content: "Wait until cities are populated for delivery and visible",
            trigger: '#city_id:visible option:not([value=""])',
        },
        {
            content: "Pick Beta City for delivery",
            trigger: "#city_id",
            run() {
                setSelectByLabel("#city_id", "Beta City", true);
            },
        },
        {
            content: "Fill mandatory fields for delivery",
            trigger: 'input[name="name"]',
            run() {
                document.querySelector('input[name="name"]').value = "Delivery User";
                document.querySelector('input[name="street"]').value = "Delivery Street";
            },
        },
        {
            content: "Confirm delivery address",
            trigger: '.oe_cart button[type="submit"]',
            run: "click",
        },
        {
            content: "Verify we have both addresses",
            trigger: ".address-item",
        },
    ],
});
