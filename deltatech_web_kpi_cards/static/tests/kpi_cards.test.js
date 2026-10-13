import {describe, expect, test} from "@odoo/hoot";
import {click, queryAll, queryAllTexts, queryOne} from "@odoo/hoot-dom";
import {animationFrame} from "@odoo/hoot-mock";
import {Component, xml} from "@odoo/owl";
import {
    defineModels,
    fields,
    getFacetTexts,
    makeMockEnv,
    models,
    mountWithCleanup,
    mountWithSearch,
} from "@web/../tests/web_test_helpers";
import {
    KpiCards,
    formatKpiAmount,
    formatKpiCount,
    formatKpiDelta,
    kpiSparklinePoints,
    useKpiCardFilters,
} from "@deltatech_web_kpi_cards/kpi_cards/kpi_cards.esm";
import {SearchBar} from "@web/search/search_bar/search_bar";

class Parcel extends models.Model {
    name = fields.Char();
    state = fields.Selection({
        selection: [
            ["transit", "Transit"],
            ["delivered", "Delivered"],
        ],
    });

    _records = [
        {id: 1, name: "P-TRANSIT", state: "transit"},
        {id: 2, name: "P-DELIVERED", state: "delivered"},
    ];
}

defineModels([Parcel]);

describe("deltatech_web_kpi_cards", () => {
    test("deltatech_web_kpi_cards: cards render counts, amounts and tones", async () => {
        await mountWithCleanup(KpiCards, {
            props: {
                cards: [
                    {key: "a", label: "In Transit", count: 6, icon: "fa-truck", tone: "info"},
                    {key: "b", label: "Returned", count: 0, tone: "purple"},
                    {key: "c", label: "COD", amounts: ["851 lei", "40 €"], subtitle: "3 AWB", tone: "action"},
                    {key: "d", label: "Unknown tone", count: 1, tone: "nope", active: true},
                ],
            },
        });
        expect(queryAll(".o_kpi_card")).toHaveLength(4);
        // Amounts, one line per currency
        expect(queryAllTexts(".o_kpi_card_value")).toEqual(["6", "0", "851 lei\n40 €", "1"]);
        expect(".o_kpi_card[data-card='a']").toHaveClass("o_kpi_card_info");
        expect(".o_kpi_card[data-card='a'] .fa-truck").toHaveCount(1);
        expect(".o_kpi_card[data-card='b']").toHaveClass("o_kpi_card_zero");
        expect(".o_kpi_card[data-card='c']").not.toHaveClass("o_kpi_card_zero");
        expect(queryOne(".o_kpi_card[data-card='c']")).toHaveText(/3 AWB/);
        // An unknown tone falls back to the neutral one
        expect(".o_kpi_card[data-card='d']").toHaveClass("o_kpi_card_slate");
        expect(".o_kpi_card[data-card='d']").toHaveClass("active");
        expect(".o_kpi_card[data-card='d']").toHaveAttribute("aria-pressed", "true");
    });

    test("deltatech_web_kpi_cards: large numbers are shown compact", async () => {
        // The compact units (k, M) are translated: the env loads the translations
        await makeMockEnv();
        const nbsp = "\u00a0";
        // Below 100 000 whole, with the currency on its side (1: $ before, 2: € after)
        expect(formatKpiAmount(851.4, 2)).toBe(`851${nbsp}€`);
        expect(formatKpiAmount(18885, 1)).toBe(`$${nbsp}18,885`);
        // From 100 000 on, in thousands or millions
        expect(formatKpiAmount(1903202, 2)).toBe(`1.9M${nbsp}€`);
        expect(formatKpiAmount(30838468, 1)).toBe(`$${nbsp}30.8M`);
        expect(formatKpiAmount(250000, 2)).toBe(`250k${nbsp}€`);
        expect(formatKpiCount(9227)).toBe("9,227");
        expect(formatKpiCount(123456)).toBe("123.5k");
        await mountWithCleanup(KpiCards, {
            props: {cards: [{key: "a", label: "Big", count: 2000000, title: "2,000,000 parcels"}]},
        });
        expect(".o_kpi_card_value").toHaveText("2M");
        expect(".o_kpi_card").toHaveAttribute("title", "2,000,000 parcels");
    });

    test("deltatech_web_kpi_cards: change, progress and trend are drawn only when given", async () => {
        await mountWithCleanup(KpiCards, {
            props: {
                cards: [
                    {key: "plain", label: "Plain", count: 5},
                    {
                        key: "up",
                        label: "Up",
                        count: 120,
                        tone: "info",
                        delta: 93.75,
                        deltaLabel: "vs previous period",
                        progress: 80,
                        progressLabel: "Target 150 (80%)",
                        trend: [1, 2, 3],
                    },
                    {key: "down", label: "Down", count: 1, delta: -4},
                    {key: "flat", label: "Flat", count: 1, delta: 0, progress: 250},
                ],
            },
        });
        // A card without the extras is what it always was
        expect(".o_kpi_card[data-card='plain'] .o_kpi_card_delta").toHaveCount(0);
        expect(".o_kpi_card[data-card='plain'] .o_kpi_card_progress").toHaveCount(0);
        expect(".o_kpi_card[data-card='plain'] .o_kpi_card_spark").toHaveCount(0);

        expect(".o_kpi_card[data-card='up'] .o_kpi_card_delta").toHaveClass("o_kpi_card_delta_up");
        expect(".o_kpi_card[data-card='up'] .o_kpi_card_delta").toHaveText(/\+93\.8%\s*vs previous period/);
        expect(".o_kpi_card[data-card='up'] .fa-caret-up").toHaveCount(1);
        expect(".o_kpi_card[data-card='up'] .o_kpi_card_progress_bar").toHaveAttribute("style", "width: 80%");
        expect(queryOne(".o_kpi_card[data-card='up']")).toHaveText(/Target 150 \(80%\)/);
        expect(".o_kpi_card[data-card='up'] .o_kpi_card_spark polyline").toHaveAttribute(
            "points",
            "0.00,27.00 50.00,14.00 100.00,1.00"
        );

        expect(".o_kpi_card[data-card='down'] .o_kpi_card_delta").toHaveClass("o_kpi_card_delta_down");
        expect(".o_kpi_card[data-card='down'] .fa-caret-down").toHaveCount(1);
        // Flat: no colour class; a progress beyond the target never overflows the bar
        expect(".o_kpi_card[data-card='flat'] .o_kpi_card_delta").not.toHaveClass("o_kpi_card_delta_up");
        expect(".o_kpi_card[data-card='flat'] .o_kpi_card_delta").not.toHaveClass("o_kpi_card_delta_down");
        expect(".o_kpi_card[data-card='flat'] .o_kpi_card_progress").toHaveAttribute("aria-valuenow", "100");
    });

    test("deltatech_web_kpi_cards: delta and sparkline helpers", async () => {
        await makeMockEnv();
        expect(formatKpiDelta(93.75)).toBe("+93.8%");
        expect(formatKpiDelta(-4)).toBe("-4%");
        expect(formatKpiDelta(0)).toBe("0%");
        // Fewer than two values: nothing to draw
        expect(kpiSparklinePoints(undefined)).toBe("");
        expect(kpiSparklinePoints([5])).toBe("");
        // A rising series runs from the bottom to the top of the box
        expect(kpiSparklinePoints([1, 2, 3])).toBe("0.00,27.00 50.00,14.00 100.00,1.00");
        // A flat series is drawn in the middle
        expect(kpiSparklinePoints([4, 4, 4])).toBe("0.00,14.00 50.00,14.00 100.00,14.00");
    });

    test("deltatech_web_kpi_cards: a click hands the card over", async () => {
        await mountWithCleanup(KpiCards, {
            props: {
                cards: [{key: "a", label: "A", count: 1}],
                onCardClick: (card) => expect.step(card.key),
            },
        });
        await click(".o_kpi_card[data-card='a']");
        expect.verifySteps(["a"]);
    });

    test("deltatech_web_kpi_cards: cards toggle their filters, one at a time", async () => {
        const FILTERS = ["kpi_transit", "kpi_delivered"];

        class Band extends Component {
            static template = xml`
                <div>
                    <SearchBar/>
                    <KpiCards cards="cards" onCardClick.bind="onCardClick"/>
                    <p class="o_test_domain" t-out="domainText"/>
                </div>`;
            static components = {KpiCards, SearchBar};
            static props = ["*"];
            setup() {
                this.filters = useKpiCardFilters(FILTERS);
            }
            get domainText() {
                return JSON.stringify(this.props.domain);
            }
            get cards() {
                return FILTERS.map((name) => ({
                    key: name,
                    label: name,
                    count: 1,
                    active: this.filters.isActive(name),
                }));
            }
            onCardClick(card) {
                this.filters.toggle(card.key);
            }
        }

        await mountWithSearch(Band, {
            resModel: "parcel",
            searchViewArch: `
                <search>
                    <filter name="mine" string="Mine" domain="[('id', '>', 0)]"/>
                    <separator/>
                    <filter name="kpi_transit" string="Transit" domain="[('state', '=', 'transit')]"/>
                    <filter name="kpi_delivered" string="Delivered" domain="[('state', '=', 'delivered')]"/>
                </search>`,
            context: {search_default_mine: 1},
        });
        expect(getFacetTexts()).toEqual(["Mine"]);

        await click(".o_kpi_card[data-card='kpi_transit']");
        await animationFrame();
        expect(getFacetTexts()).toEqual(["Mine", "Transit"]);
        expect(".o_test_domain").toHaveText(/transit/);
        expect(".o_kpi_card[data-card='kpi_transit']").toHaveClass("active");

        // Another card replaces the filter instead of adding to it
        await click(".o_kpi_card[data-card='kpi_delivered']");
        await animationFrame();
        expect(getFacetTexts()).toEqual(["Mine", "Delivered"]);
        expect(".o_test_domain").not.toHaveText(/transit/);
        expect(".o_kpi_card[data-card='kpi_transit']").not.toHaveClass("active");
        expect(".o_kpi_card[data-card='kpi_delivered']").toHaveClass("active");

        // A second click clears it; the user's own filter stays
        await click(".o_kpi_card[data-card='kpi_delivered']");
        await animationFrame();
        expect(getFacetTexts()).toEqual(["Mine"]);
        expect(".o_kpi_card.active").toHaveCount(0);
    });
});
