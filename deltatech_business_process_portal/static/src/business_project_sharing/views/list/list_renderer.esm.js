/** @odoo-module */

import {ListRenderer} from "@web/views/list/list_renderer";
// Import {evalDomain} from "@web/views/utils";

const {onWillUpdateProps} = owl;

export class BusinessProjectSharingListRenderer extends ListRenderer {
    setup() {
        super.setup(...arguments);
        this.setColumns(this.allColumns);
        onWillUpdateProps((nextProps) => {
            this.setColumns(nextProps.archInfo.columns);
        });
    }

    setColumns(columns) {
        if (this.props.list.records.length) {
            const allColumns = [];
            // Const firstRecord = this.props.list.records[0];
            for (const column of columns) {
                allColumns.push(column);
            }
            this.allColumns = allColumns;
        } else {
            this.allColumns = columns;
        }
        this.state.columns = this.allColumns.filter((col) => !col.optional || this.optionalActiveFields[col.name]);
    }
}
