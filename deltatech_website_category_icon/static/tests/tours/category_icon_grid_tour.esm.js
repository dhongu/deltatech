import {
    changeOptionInPopover,
    clickOnSave,
    clickOnSnippet,
    insertSnippet,
    registerWebsitePreviewTour,
} from "@website/js/tours/tour_utils";

const snippet = {id: "s_category_icon_grid", name: "Category Icon Grid", groupName: "Catalog"};

registerWebsitePreviewTour(
    "deltatech_website_category_icon.category_icon_grid",
    {
        url: "/",
        edition: true,
    },
    () => [
        ...insertSnippet(snippet),
        {
            content: "The grid shows the main categories of the database, with their icon",
            trigger: ":iframe .s_category_icon_grid a.s_category_icon_grid_item:contains(TB Grid Tractors) svg",
        },
        ...clickOnSnippet(snippet),
        ...changeOptionInPopover("Category Icon Grid", "Icon Size", "Large"),
        {
            trigger: ":iframe .s_category_icon_grid.s_category_icon_grid_icon_lg",
        },
        ...changeOptionInPopover("Category Icon Grid", "Categories", "Chosen categories"),
        {
            content: "Nothing chosen yet: the editor asks for categories",
            trigger: ":iframe .s_category_icon_grid[data-mode=manual] .s_category_icon_grid_empty:not(.d-none)",
        },
        {
            trigger: "[data-container-title='Category Icon Grid'] .o-hb-selectMany2X-toggle",
            run: "click",
        },
        {
            trigger: ".o_popover input",
            run: "edit TB Grid Seeds",
        },
        {
            trigger: ".o_popover .o-dropdown-item:contains(TB Grid Seeds)",
            run: "click",
        },
        {
            content: "Only the chosen category is shown",
            trigger:
                ":iframe .s_category_icon_grid_row:not(:has(a:contains(TB Grid Tractors))) a.s_category_icon_grid_item:contains(TB Grid Seeds)",
        },
        ...clickOnSave(),
        {
            content: "After saving, the page renders the grid again from the database",
            trigger:
                ":iframe body:not(.editor_enable) .s_category_icon_grid a.s_category_icon_grid_item:contains(TB Grid Seeds)",
        },
    ]
);
