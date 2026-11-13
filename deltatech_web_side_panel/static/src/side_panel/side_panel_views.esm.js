/** @odoo-module **/
// ©  2026 Deltatech
// See README.rst file on addons root folder for license details
import {KanbanController} from "@web/views/kanban/kanban_controller";
import {ListController} from "@web/views/list/list_controller";
import {kanbanView} from "@web/views/kanban/kanban_view";
import {listView} from "@web/views/list/list_view";
import {registry} from "@web/core/registry";
import {withSidePanel} from "./side_panel_controller.esm";

export const SidePanelKanbanController = withSidePanel(KanbanController, "deltatech_web_side_panel.KanbanView");
export const SidePanelListController = withSidePanel(ListController, "deltatech_web_side_panel.ListView");

export const sidePanelKanbanView = {...kanbanView, Controller: SidePanelKanbanController};
export const sidePanelListView = {...listView, Controller: SidePanelListController};

registry.category("views").add("side_panel_kanban", sidePanelKanbanView);
registry.category("views").add("side_panel_list", sidePanelListView);
