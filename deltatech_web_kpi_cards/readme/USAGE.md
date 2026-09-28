For developers. Add `deltatech_web_kpi_cards` to `depends`, then show the cards from any OWL
component, for instance a list renderer:

```js
import {KpiCards, useKpiCardFilters} from "@deltatech_web_kpi_cards/kpi_cards/kpi_cards.esm";

const FILTERS = ["filter_late", "filter_today"];

class MyDashboard extends Component {
    static template = xml`<KpiCards cards="cards" onCardClick.bind="onCardClick"/>`;
    static components = {KpiCards};
    setup() {
        this.filters = useKpiCardFilters(FILTERS);
    }
    get cards() {
        return [
            {key: "filter_late", label: "Late", count: 4, icon: "fa-clock-o", tone: "warning",
             active: this.filters.isActive("filter_late")},
        ];
    }
    onCardClick(card) {
        this.filters.toggle(card.key);
    }
}
```

A card: `key` (also its `data-card` attribute), `label`, then `count` or `amounts` (formatted
strings), optional `subtitle`, `icon` (a Font Awesome class) and `tone`: `info`, `success`,
`warning`, `danger`, `purple`, `action` or `slate` (the default).

Keep the card filters in a group of their own in the search view, a `<separator/>` before and
after them: a click clears the group of the active card filter, and nothing else.

What a card counts belongs to the module that shows it: give the card and its filter the same
server-side domain, and the number on the card is the number of rows the click opens.
