/** @odoo-module **/
// ©  2026 Deltatech
// See README.rst file on addons root folder for license details
import {Component, useSubEnv} from "@odoo/owl";
import {View, getDefaultConfig} from "@web/views/view";

/**
 * The panel shown next to a kanban or a list: the form view of the selected record,
 * read-only, with the buttons to move between records, open the full form, refresh
 * and close.
 */
export class SidePanel extends Component {
    static template = "deltatech_web_side_panel.SidePanel";
    static components = {View};
    static props = {
        resModel: String,
        resId: Number,
        formViewRef: {type: [String, Boolean], optional: true},
        position: Number,
        total: Number,
        onClose: Function,
        onPrev: Function,
        onNext: Function,
        onOpen: Function,
        onRefresh: Function,
    };

    setup() {
        // A view writes into env.config (the breadcrumb title, the views list): give the
        // embedded form its own, so that it leaves the page's breadcrumb alone.
        useSubEnv({config: getDefaultConfig()});
    }

    get positionLabel() {
        return `${this.props.position} / ${this.props.total}`;
    }

    get viewProps() {
        const context = {};
        if (this.props.formViewRef) {
            // Odoo resolves the xml id of the form view on the server.
            context.form_view_ref = this.props.formViewRef;
        }
        return {
            type: "form",
            resModel: this.props.resModel,
            resId: this.props.resId,
            context,
            display: {controlPanel: false},
            readonly: true,
        };
    }
}
