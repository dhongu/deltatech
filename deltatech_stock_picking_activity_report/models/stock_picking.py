import re
import logging
from datetime import datetime
from odoo import models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _log_activity(self, log_msg):
        try:
            if self.env.user.has_group("base.group_user") and self.env.user.login != "__system__":
                today = datetime.now().date()
                now = datetime.now().strftime("%H:%M:%S")
                full_log_msg = f"{now} - {log_msg}\n"
                for picking in self:
                    picking_id = picking.id
                    existing_record = (
                        self.env["stock.picking.activity.record"]
                        .sudo()
                        .search(
                            [
                                ("picking_id", "=", picking_id),
                                ("change_date", "=", today),
                                ("user_id", "=", self.env.user.id),
                            ],
                            limit=1,
                        )
                    )

                    vals = {
                        "state": picking.state,
                    }

                    if not existing_record:
                        vals.update(
                            {
                                "picking_id": picking_id,
                                "change_date": today,
                                "user_id": self.env.user.id,
                                "activity_log": full_log_msg,
                            }
                        )
                        if self.env.context.get("chatter_message", False):
                            vals.update({"chatter_message": True})
                        if self.env.context.get("exit_product_number", False):
                            vals.update({"exit_product_number": self.env.context.get("exit_product_number")})
                        if self.env.context.get("entry_product_number", False):
                            vals.update({"entry_product_number": self.env.context.get("entry_product_number")})
                        if self.env.context.get("internal_product_number", False):
                            vals.update({"internal_product_number": self.env.context.get("internal_product_number")})
                        if self.env.context.get("has_validated", False):
                            vals.update({"has_validated": True})
                        self.env["stock.picking.activity.record"].sudo().create(vals)
                    else:
                        new_log = (existing_record.activity_log or "") + full_log_msg
                        vals["activity_log"] = new_log
                        if self.env.context.get("chatter_message", False):
                            vals.update({"chatter_message": True})
                        if self.env.context.get("exit_product_number", False):
                            vals.update(
                                {
                                    "exit_product_number": existing_record.exit_product_number
                                    + self.env.context.get("exit_product_number")
                                }
                            )
                        if self.env.context.get("entry_product_number", False):
                            vals.update(
                                {
                                    "entry_product_number": existing_record.entry_product_number
                                    + self.env.context.get("entry_product_number")
                                }
                            )
                        if self.env.context.get("internal_product_number", False):
                            vals.update(
                                {
                                    "internal_product_number": existing_record.internal_product_number
                                    + self.env.context.get("internal_product_number")
                                }
                            )
                        if self.env.context.get("has_validated", False):
                            vals.update({"has_validated": True})
                        existing_record.sudo().write(vals)
        except Exception:
            _logger.exception("Error while logging activity")

    def write(self, vals):
        try:
            if self.env.user.has_group("base.group_user") and self.env.user.login != "__system__":
                fields_info = self.fields_get(list(vals.keys()))
                for picking in self:
                    changes = []
                    log_context = {}
                    for field_name, new_val in vals.items():
                        field_label = fields_info.get(field_name, {}).get("string", field_name)
                        field_type = fields_info.get(field_name, {}).get("type")
                        old_val = picking[field_name]

                        def format_val(val, f_type, f_name):
                            if not val:
                                return "None"
                            if f_type == "many2one":
                                if isinstance(val, int):
                                    try:
                                        target_model = fields_info[f_name]["relation"]
                                        return self.env[target_model].browse(val).display_name or f"ID: {val}"
                                    except Exception:
                                        return f"ID: {val}"
                                return val.display_name or f"ID: {val.id}"
                            elif f_type == "selection":
                                selection = fields_info[f_name].get("selection", [])
                                return dict(selection).get(val, val)
                            elif f_type in ["one2many", "many2many"]:
                                formatted_commands = []
                                target_model_name = fields_info[f_name]["relation"]
                                target_model = self.env[target_model_name]
                                target_fields_info = target_model.fields_get()

                                def format_sub_val(sub_val, sub_f_type, sub_f_name):
                                    if not sub_val:
                                        return "None"
                                    if sub_f_type == "many2one":
                                        if isinstance(sub_val, int):
                                            try:
                                                sub_target_model = target_fields_info[sub_f_name]["relation"]
                                                return (
                                                    self.env[sub_target_model].browse(sub_val).display_name
                                                    or f"ID: {sub_val}"
                                                )
                                            except Exception:
                                                return f"ID: {sub_val}"
                                        return sub_val.display_name or f"ID: {sub_val.id}"
                                    elif sub_f_type == "selection":
                                        selection = target_fields_info[sub_f_name].get("selection", [])
                                        return dict(selection).get(sub_val, sub_val)
                                    return str(sub_val)

                                for command in val:
                                    if not isinstance(command, list | tuple) or len(command) == 0:
                                        continue
                                    cmd_type = command[0]
                                    if cmd_type == 0:  # CREATE
                                        data = command[2]
                                        readable_data = []
                                        for fname, fval in data.items():
                                            f_info = target_fields_info.get(fname, {})
                                            flabel = f_info.get("string", fname)
                                            f_type = f_info.get("type")
                                            readable_data.append(f"{flabel}: {format_sub_val(fval, f_type, fname)}")

                                        name_part = ""
                                        if "product_id" in data:
                                            p = self.env["product.product"].browse(data["product_id"])
                                            name_part = f" ({p.display_name})"
                                        elif "name" in data:
                                            name_part = f" ({data['name']})"

                                        formatted_commands.append(f"Add New{name_part}: [{', '.join(readable_data)}]")
                                    elif cmd_type == 1:  # UPDATE
                                        line_id = command[1]
                                        data = command[2]
                                        line = target_model.browse(line_id)
                                        name_part = line.display_name or f"ID {line_id}"
                                        readable_data = []
                                        for fname, fval in data.items():
                                            f_info = target_fields_info.get(fname, {})
                                            flabel = f_info.get("string", fname)
                                            f_type = f_info.get("type")
                                            readable_data.append(f"{flabel}: {format_sub_val(fval, f_type, fname)}")
                                        formatted_commands.append(f"Update {name_part}: [{', '.join(readable_data)}]")
                                    elif cmd_type == 2:  # DELETE
                                        line_id = command[1]
                                        line = target_model.browse(line_id)
                                        name_part = line.display_name or f"ID {line_id}"
                                        formatted_commands.append(f"Delete {name_part}")
                                    elif cmd_type == 3:  # UNLINK
                                        line_id = command[1]
                                        line = target_model.browse(line_id)
                                        name_part = line.display_name or f"ID {line_id}"
                                        formatted_commands.append(f"Remove {name_part}")
                                    elif cmd_type == 4:  # LINK
                                        line_id = command[1]
                                        line = target_model.browse(line_id)
                                        name_part = line.display_name or f"ID {line_id}"
                                        formatted_commands.append(f"Link {name_part}")
                                    elif cmd_type == 5:  # UNLINK ALL
                                        formatted_commands.append("Remove all")
                                    elif cmd_type == 6:  # REPLACE ALL
                                        formatted_commands.append(f"Replace all with IDs {command[2]}")
                                return " | ".join(formatted_commands) if formatted_commands else str(val)

                            return str(val)

                        old_val_str = format_val(old_val, field_type, field_name)
                        new_val_str = format_val(new_val, field_type, field_name)

                        if old_val_str != new_val_str:
                            changes.append(f"{field_label}: {old_val_str} -> {new_val_str}")

                    if changes:
                        picking.with_context(**log_context)._log_activity("Updated: " + ", ".join(changes))
        except Exception:
            _logger.exception("Error while logging activity in write")

        return super().write(vals)

    def message_post(self, **kwargs):
        res = super().message_post(**kwargs)
        body = kwargs.get("body", "")
        if body:
            clean_body = re.sub("<.*?>", "", body)
            if clean_body.strip():
                self.with_context(chatter_message=True)._log_activity(f"Message: {clean_body.strip()}")
        return res

    def action_confirm(self):
        res = super().action_confirm()
        self._log_activity("Button Clicked: Confirm")
        return res

    def action_assign(self):
        res = super().action_assign()
        self._log_activity("Button Clicked: Check Availability")
        return res

    def button_validate(self):
        res = super().button_validate()
        for picking in self:
            counted_product_number = 0
            log_context = {"has_validated": True}
            for line in picking.move_ids_without_package:
                counted_product_number += line.quantity
            if picking.picking_type_id.code == "outgoing":
                log_context["exit_product_number"]=counted_product_number
                self.with_context(**log_context)._log_activity("Button Clicked: Validate")
            if picking.picking_type_id.code == "incoming":
                log_context["entry_product_number"]=counted_product_number
                self.with_context(**log_context)._log_activity("Button Clicked: Validate")
            if picking.picking_type_id.code == "internal":
                log_context["internal_product_number"]=counted_product_number
                self.with_context(log_context)._log_activity("Button Clicked: Validate")
        return res

    def action_cancel(self):
        res = super().action_cancel()
        self._log_activity("Button Clicked: Cancel")
        return res
