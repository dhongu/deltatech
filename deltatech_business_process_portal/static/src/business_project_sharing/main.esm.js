/** @odoo-module **/
import {startWebClient} from "@web/start";
import {BusinessProjectSharingWebClient} from "./business_project_sharing.esm";
import {prepareFavoriteMenuRegister} from "./components/favorite_menu_registry.esm";

prepareFavoriteMenuRegister();
startWebClient(BusinessProjectSharingWebClient);
