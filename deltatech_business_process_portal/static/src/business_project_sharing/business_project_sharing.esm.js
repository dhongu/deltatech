/** @odoo-module **/
import {useBus, useService} from "@web/core/utils/hooks";
import {ActionContainer} from "@web/webclient/actions/action_container";
import {MainComponentsContainer} from "@web/core/main_components_container";
import {useOwnDebugContext} from "@web/core/debug/debug_context";
import {session} from "@web/session";

const {Component, useEffect, useExternalListener, useState} = owl;

export class BusinessProjectSharingWebClient extends Component {
    setup() {
        window.parent.document.body.style.margin = "0"; // Remove the margin in the parent body
        this.actionService = useService("action");
        this.user = useService("user");
        useService("legacy_service_provider");
        useOwnDebugContext({categories: ["default"]});
        this.state = useState({
            fullscreen: false,
        });
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", (mode) => {
            if (mode !== "new") {
                this.state.fullscreen = mode === "fullscreen";
            }
        });
        useEffect(
            () => {
                this._showView();
            },
            () => []
        );
        useExternalListener(window, "click", this.onGlobalClick, {capture: true});
    }

    async _showView() {
        const {action_name, business_project_sharing_id, open_business_project_action} = session;
        await this.actionService.doAction(action_name, {
            clearBreadcrumbs: true,
            additionalContext: {
                active_id: business_project_sharing_id,
            },
        });
        if (open_business_project_action) {
            await this.actionService.doAction(open_business_project_action, {
                clearBreadcrumbs: true,
                additionalContext: {
                    active_id: business_project_sharing_id,
                },
            });
        }
    }

    /**
     * @param {MouseEvent} ev
     */
    onGlobalClick(ev) {
        // When a ctrl-click occurs inside an <a href/> element
        // we let the browser do the default behavior and
        // we do not want any other listener to execute.
        if (
            ev.ctrlKey &&
            ((ev.target instanceof HTMLAnchorElement && ev.target.href) ||
                (ev.target instanceof HTMLElement && ev.target.closest("a[href]:not([href=''])")))
        ) {
            ev.stopImmediatePropagation();
            return;
        }
    }
}

BusinessProjectSharingWebClient.components = {ActionContainer, MainComponentsContainer};
BusinessProjectSharingWebClient.template = "deltatech_business_process_portal.BusinessProjectSharingWebClient";
