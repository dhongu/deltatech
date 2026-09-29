import {Component, t, useProps} from "@odoo/owl";
import {useEnv} from "@web/owl2/utils";
import {formatCurrency} from "@web/core/currency";
import {humanNumber} from "@web/core/utils/numbers";
import {localization} from "@web/core/l10n/localization";
import {formatInteger} from "@web/views/fields/formatters";

/**
 * A band of KPI cards. Presentation only: what a card counts, and what a
 * click on it does, belong to the module that shows it.
 *
 * A card: `key` (also its `data-card`), `label`, then either `count` or
 * `amounts` (formatted lines, one per currency), optional `subtitle`,
 * `icon` (an `oi` icon name, see web/icons.py), `tone` (one of KPI_TONES),
 * `active` and `title` (the tooltip, the label by default: the place for
 * exact amounts).
 */
export const KPI_TONES = ["info", "success", "warning", "danger", "purple", "action", "slate"];

// From this value on, a number is shown in thousands or millions (Odoo's
// own humanNumber: 1.9M, 123.5k), so that it fits on a card.
export const KPI_COMPACT_FROM = 100000;

// HumanNumber keeps its decimal below a thousand: 250.0k reads better as 250k
function dropZeroDecimal(text) {
    return text.replace(`${localization.decimalPoint}0k`, "k").replace(`${localization.decimalPoint}0M`, "M");
}

/**
 * An amount as a card shows it: whole below KPI_COMPACT_FROM (851 lei),
 * compact from there on (1.9M lei), with the currency where it belongs.
 */
export function formatKpiAmount(amount, currencyId) {
    const options = Math.abs(amount) >= KPI_COMPACT_FROM ? {humanReadable: true, digits: [16, 1]} : {digits: [16, 0]};
    return dropZeroDecimal(formatCurrency(amount, currencyId, options));
}

/** A count as a card shows it: 9,227, then 123.5k. */
export function formatKpiCount(count) {
    return Math.abs(count) >= KPI_COMPACT_FROM
        ? dropZeroDecimal(humanNumber(count, {decimals: 1}))
        : formatInteger(count);
}

export class KpiCards extends Component {
    static template = "deltatech_web_kpi_cards.KpiCards";
    // Owl 3: props are declared with useProps (a static props throws)
    props = useProps({
        cards: t.array(),
        onCardClick: t.function().optional(),
    });

    toneOf(card) {
        return KPI_TONES.includes(card.tone) ? card.tone : "slate";
    }

    formatCount(count) {
        return formatKpiCount(count || 0);
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
