/* @odoo-module */

import {StaticList} from "@web/model/relational_model/static_list";
import {patch} from "@web/core/utils/patch";
import {x2ManyCommands} from "@web/core/orm_service";

patch(StaticList.prototype, {
    _applyCommands() {
        const result = super._applyCommands(...arguments);
        // A second delete of an unsaved line (e.g. Enter pressed twice on the trash) no longer
        // finds its CREATE command and keeps a DELETE with the virtual id, which the server
        // sends to SQL as `DELETE ... WHERE id IN ('virtual_N')`. The line was never saved.
        const {DELETE, UNLINK} = x2ManyCommands;
        this._commands = this._commands.filter(
            (command) => ![DELETE, UNLINK].includes(command[0]) || typeof command[1] !== "string"
        );
        return result;
    },
});
