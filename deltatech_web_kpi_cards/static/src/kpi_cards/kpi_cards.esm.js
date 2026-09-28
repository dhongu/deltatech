import {Component, useEnv} from "@odoo/owl";

/**
 * A band of KPI cards. Presentation only: what a card counts, and what a
 * click on it does, belong to the module that shows it.
 *
 * A card: `key` (also its `data-card`), `label`, then either `count` or
 * `amounts` (formatted lines, one per currency), optional `subtitle`,
 * `icon` (a Font Awesome class), `tone` (one of KPI_TONES) and `active`.
 */
export const KPI_TONES = ["info", "success", "warning", "danger", "purple", "action", "slate"];

export class KpiCards extends Component {
    static template = "deltatech_web_kpi_cards.KpiCards";
    static props = {
        cards: {
            type: Array,
            element: {
                type: Object,
                shape: {
                    key: String,
                    label: String,
                    count: {type: Number, optional: true},
                    amounts: {type: Array, element: String, optional: true},
                    subtitle: {type: String, optional: true},
                    icon: {type: String, optional: true},
                    tone: {type: String, optional: true},
                    active: {type: Boolean, optional: true},
                    "*": true,
                },
            },
        },
        onCardClick: {type: Function, optional: true},
    };

    toneOf(card) {
        return KPI_TONES.includes(card.tone) ? card.tone : "slate";
    }

    isZero(card) {
        return card.amounts ? !card.amounts.length : !card.count;
    }

    onClick(card) {
        if (this.props.onCardClick) {
            this.props.onCardClick(card);
        }
    }
}

/**
 * Binds cards to filters of the search view the component lives in.
 *
 * `toggle(name)` activates the filter `name` and drops the other card
 * filters, so that the facets of two cards never add up; a second call on
 * the same filter clears it. The user's own filters are kept, provided the
 * card filters sit in a group of their own in the search view (a
 * `<separator/>` before and after them): a group is what gets cleared.
 *
 * @param {string[] | () => string[]} filterNames the card filters
 */
export function useKpiCardFilters(filterNames) {
    const env = useEnv();
    const names = () => new Set(typeof filterNames === "function" ? filterNames() : filterNames);
    const items = () => {
        const wanted = names();
        return env.searchModel.getSearchItems((item) => item.type === "filter" && wanted.has(item.name));
    };
    return {
        isActive(name) {
            return items().some((item) => item.name === name && item.isActive);
        },
        toggle(name) {
            const searchModel = env.searchModel;
            const cardItems = items();
            const target = cardItems.find((item) => item.name === name);
            if (!target) {
                return;
            }
            const wasActive = target.isActive;
            const groups = new Set(cardItems.filter((item) => item.isActive).map((item) => item.groupId));
            for (const groupId of groups) {
                searchModel.deactivateGroup(groupId);
            }
            if (!wasActive) {
                searchModel.toggleSearchItem(target.id);
            }
        },
    };
}
