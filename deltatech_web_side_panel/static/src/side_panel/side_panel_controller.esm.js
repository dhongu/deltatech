/** @odoo-module **/
// ©  2026 Deltatech
// See README.rst file on addons root folder for license details
import {onMounted, onPatched, onWillUnmount, useState} from "@odoo/owl";
import {SIZES} from "@web/core/ui/ui_service";
import {useService} from "@web/core/utils/hooks";
import {SidePanel} from "./side_panel.esm";

/**
 * Builds a controller that shows the form of the selected record in a panel on the right.
 *
 * A click on a record selects it instead of opening its form: the controller's `openRecord`
 * is what both renderers call, so the same code serves kanban and list. The panel is off on
 * small screens, where the views behave as usual, and when the action context has
 * `disable_side_panel`. The form shown comes from the action context key `side_panel_view_ref`
 * (an xml id), else the default form view of the model.
 *
 * @param {Class} Controller the ListController or the KanbanController
 * @param {String} template the template that adds the panel next to the renderer
 * @returns {Class}
 */
export function withSidePanel(Controller, template) {
    class SidePanelController extends Controller {
        static template = template;
        static components = {...Controller.components, SidePanel};

        setup() {
            super.setup();
            this.ui = useService("ui");
            this.sidePanelState = useState({resId: false});
            onMounted(() => {
                this.syncSidePanelSelection();
                // The records are drawn again after a reload, often after this controller
                // has patched: follow the changes of the content to keep the highlight.
                const root = this.rootRef && this.rootRef.el;
                if (root) {
                    this.sidePanelObserver = new MutationObserver(() => this.scheduleSidePanelSync());
                    this.sidePanelObserver.observe(root, {childList: true, subtree: true});
                }
            });
            onPatched(() => this.syncSidePanelSelection());
            onWillUnmount(() => {
                this.sidePanelObserver?.disconnect();
                cancelAnimationFrame(this.sidePanelSyncFrame);
            });
        }

        scheduleSidePanelSync() {
            cancelAnimationFrame(this.sidePanelSyncFrame);
            this.sidePanelSyncFrame = requestAnimationFrame(() => this.syncSidePanelSelection());
        }

        get className() {
            return `${super.className || ""} o_has_side_panel`;
        }

        get sidePanelEnabled() {
            return !this.props.context?.disable_side_panel && this.ui.size >= SIZES.XL;
        }

        get sidePanelRecords() {
            // Grouped lists nest: a group's list may be grouped again, at any depth.
            const collect = (list) =>
                list.isGrouped ? list.groups.flatMap((group) => collect(group.list)) : list.records;
            return collect(this.model.root);
        }

        get sidePanelVisible() {
            const resId = this.sidePanelState.resId;
            return Boolean(
                this.sidePanelEnabled && resId && this.sidePanelRecords.some((record) => record.resId === resId)
            );
        }

        get sidePanelProps() {
            const records = this.sidePanelRecords;
            const index = records.findIndex((record) => record.resId === this.sidePanelState.resId);
            return {
                resModel: this.props.resModel,
                resId: this.sidePanelState.resId,
                formViewRef: this.props.context?.side_panel_view_ref || false,
                position: index + 1,
                total: records.length,
                onClose: () => this.closeSidePanel(),
                onPrev: () => this.moveSidePanel(-1),
                onNext: () => this.moveSidePanel(1),
                onOpen: () => this.openSidePanelRecord(),
                onRefresh: () => this.refreshSidePanel(),
            };
        }

        /**
         * Both renderers call this on a click on a record.
         */
        async openRecord(record, options = {}) {
            const known = this.sidePanelRecords.some((rec) => rec.resId === record.resId);
            if (this.sidePanelEnabled && known && !options.newWindow && !options.force) {
                this.sidePanelState.resId = record.resId;
                return undefined;
            }
            return super.openRecord(record, options);
        }

        closeSidePanel() {
            this.sidePanelState.resId = false;
        }

        moveSidePanel(delta) {
            const records = this.sidePanelRecords;
            const index = records.findIndex((record) => record.resId === this.sidePanelState.resId);
            if (index < 0 || !records.length) {
                return;
            }
            const next = records[(index + delta + records.length) % records.length];
            this.sidePanelState.resId = next.resId;
        }

        async openSidePanelRecord() {
            const record = this.sidePanelRecords.find((rec) => rec.resId === this.sidePanelState.resId);
            if (record) {
                // The original behaviour: the full form. `force` opens it even when the
                // action has no form view of its own.
                await super.openRecord(record, {force: true});
            }
        }

        async refreshSidePanel() {
            await this.model.root.load();
        }

        syncSidePanelSelection() {
            const root = this.rootRef && this.rootRef.el;
            if (!root) {
                return;
            }
            for (const el of root.querySelectorAll(".o_side_panel_selected")) {
                el.classList.remove("o_side_panel_selected");
            }
            if (!this.sidePanelVisible) {
                return;
            }
            const record = this.sidePanelRecords.find((rec) => rec.resId === this.sidePanelState.resId);
            const el = record && root.querySelector(`[data-id="${record.id}"]`);
            if (el) {
                el.classList.add("o_side_panel_selected");
            }
        }
    }
    return SidePanelController;
}
