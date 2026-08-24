# models/sale_order.py
import logging
import re
from datetime import datetime

from odoo import models

_logger = logging.getLogger(__name__)

# Tipurile de câmp care nu au ce căuta în jurnal: valoarea lor serializată e
# conținutul brut al fișierului (eticheta AWB, semnătura), adică sute de kB de
# base64 per scriere.
SKIPPED_FIELD_TYPES = ("binary",)
# Plafoane de siguranță: o valoare de câmp, un mesaj și jurnalul unei zile nu
# pot depăși aceste dimensiuni, oricât de mare ar fi conținutul scris.
MAX_VALUE_LENGTH = 200
# Câmpurile x2many (liniile comenzii) sunt descrise linie cu linie, deci au
# nevoie de un plafon mai larg — altfel s-ar pierde tocmai informația utilă.
MAX_RELATION_LENGTH = 2000
MAX_MESSAGE_LENGTH = 2000
MAX_LOG_LENGTH = 65536


def truncate(value, limit):
    """Scurtează ``value`` la ``limit`` caractere, marcând cât s-a tăiat."""
    if len(value) <= limit:
        return value
    return f"{value[:limit]}… (+{len(value) - limit} chars)"


def format_line_ref(target_model, line_id):
    """Nume lizibil pentru linia vizată de o comandă x2many.

    ``line_id`` nu este întotdeauna un id din baza de date: clientul web poate
    trimite id-ul virtual al unei linii încă nesalvate (``"virtual_7149"``).
    Un ``browse`` pe un id nenumeric ar produce un recordset cu un id per
    caracter, iar citirea lui ar arunca (``Expected singleton``), aşa că
    afişăm id-ul aşa cum a venit.
    """
    if not isinstance(line_id, int):
        return f"ID {line_id}"
    line = target_model.browse(line_id).exists()
    return line.display_name if line else f"ID {line_id}"


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _log_activity(self, log_msg):
        try:
            if self.env.user.has_group("base.group_user") and self.env.user.login != "__system__":
                today = datetime.now().date()
                now = datetime.now().strftime("%H:%M:%S")
                full_log_msg = f"{now} - {truncate(log_msg, MAX_MESSAGE_LENGTH)}\n"
                for order in self:
                    # search with sudo to ensure we find records even if current user has limited access
                    order_id = order.id
                    existing_record = (
                        self.env["sale.order.activity.record"]
                        .sudo()
                        .search(
                            [
                                ("sale_order_id", "=", order_id),
                                ("change_date", "=", today),
                                ("user_id", "=", self.env.user.id),
                            ],
                            limit=1,
                        )
                    )

                    vals = {
                        "state": order.state,
                    }

                    if not existing_record:
                        vals.update(
                            {
                                "sale_order_id": order_id,
                                "change_date": today,
                                "user_id": self.env.user.id,
                                "activity_log": full_log_msg,
                            }
                        )
                        if self.env.context.get("generated_awb", False):
                            vals.update({"awb_generated": True})
                        if self.env.context.get("chatter_message", False):
                            vals.update({"chatter_message": True})
                        if self.env.context.get("tags_changed", False):
                            vals.update({"tags_changed": True})
                        if self.env.context.get("stage", False):
                            vals.update({"stage": self.env.context.get("stage")})
                        self.env["sale.order.activity.record"].sudo().create(vals)
                    else:
                        new_log = (existing_record.activity_log or "") + full_log_msg
                        if len(new_log) > MAX_LOG_LENGTH:
                            # Păstrăm coada (activitatea recentă) și tăiem de la
                            # prima linie completă, ca jurnalul să rămână lizibil.
                            new_log = new_log[-MAX_LOG_LENGTH:].split("\n", 1)[-1]
                        vals["activity_log"] = new_log
                        if self.env.context.get("generated_awb", False):
                            vals["awb_generated"] = True
                        if self.env.context.get("chatter_message", False):
                            vals.update({"chatter_message": True})
                        if self.env.context.get("tags_changed", False):
                            vals.update({"tags_changed": True})
                        if self.env.context.get("stage", False):
                            vals.update({"stage": self.env.context.get("stage")})
                        existing_record.sudo().write(vals)
        except Exception:
            _logger.exception("Error while logging activity")

    def write(self, vals):
        # Prepare readable log before write to capture old values
        try:
            if self.env.user.has_group("base.group_user") and self.env.user.login != "__system__":
                fields_info = self.fields_get(list(vals.keys()))
                for order in self:
                    changes = []
                    log_context = {}
                    for field_name, new_val in vals.items():
                        field_label = fields_info.get(field_name, {}).get("string", field_name)
                        field_type = fields_info.get(field_name, {}).get("type")
                        if field_type in SKIPPED_FIELD_TYPES:
                            # Ieșim înainte de a citi valoarea veche: pentru un câmp
                            # binar, `order[field_name]` ar încărca degeaba din
                            # filestore un conținut pe care oricum nu-l jurnalizăm.
                            continue
                        old_val = order[field_name]

                        if field_name == "stage" and new_val == "pre_advice":
                            log_context["generated_awb"] = True
                            log_context["stage"] = order.stage
                        if field_name == "tag_ids":
                            log_context["tags_changed"] = True

                        # Simple formatting for old/new values
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
                                if not isinstance(val, models.Model):
                                    # id virtual sau altă valoare brută venită de la client
                                    return f"ID: {val}"
                                return val.display_name or f"ID: {val.id}"
                            elif f_type == "selection":
                                selection = fields_info[f_name].get("selection", [])
                                return dict(selection).get(val, val)
                            elif f_type in ["one2many", "many2many"]:
                                # Handle Odoo command list for x2many fields
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
                                        if not isinstance(sub_val, models.Model):
                                            # id virtual sau altă valoare brută venită de la client
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
                                        name_part = format_line_ref(target_model, line_id)

                                        readable_data = []
                                        for fname, fval in data.items():
                                            f_info = target_fields_info.get(fname, {})
                                            flabel = f_info.get("string", fname)
                                            f_type = f_info.get("type")
                                            readable_data.append(f"{flabel}: {format_sub_val(fval, f_type, fname)}")

                                        formatted_commands.append(f"Update {name_part}: [{', '.join(readable_data)}]")
                                    elif cmd_type == 2:  # DELETE
                                        name_part = format_line_ref(target_model, command[1])
                                        formatted_commands.append(f"Delete {name_part}")
                                    elif cmd_type == 3:  # UNLINK (remove from relation, but don't delete)
                                        name_part = format_line_ref(target_model, command[1])
                                        formatted_commands.append(f"Remove {name_part}")
                                    elif cmd_type == 4:  # LINK (add existing)
                                        name_part = format_line_ref(target_model, command[1])
                                        formatted_commands.append(f"Link {name_part}")
                                    elif cmd_type == 5:  # UNLINK ALL
                                        formatted_commands.append("Remove all")
                                    elif cmd_type == 6:  # REPLACE ALL
                                        formatted_commands.append(f"Replace all with IDs {command[2]}")
                                return " | ".join(formatted_commands) if formatted_commands else str(val)

                            return str(val)

                        if field_name == "shipment_info":
                            changes.append("Shipment Info updated")
                        else:
                            limit = MAX_RELATION_LENGTH if field_type in ("one2many", "many2many") else MAX_VALUE_LENGTH
                            old_val_str = truncate(format_val(old_val, field_type, field_name), limit)
                            new_val_str = truncate(format_val(new_val, field_type, field_name), limit)

                            if old_val_str != new_val_str:
                                changes.append(f"{field_label}: {old_val_str} -> {new_val_str}")

                    if changes:
                        order.with_context(**log_context)._log_activity("Updated: " + ", ".join(changes))
        except Exception:
            _logger.exception("Error while logging activity in write")

        return super().write(vals)

    def message_post(self, **kwargs):
        res = super().message_post(**kwargs)
        body = kwargs.get("body", "")
        if body:
            # Clean HTML tags
            clean_body = re.sub("<.*?>", "", body)
            if clean_body.strip():
                self.with_context(chatter_message=True)._log_activity(f"Message: {clean_body.strip()}")
        return res

    def action_confirm(self):
        res = super().action_confirm()
        self._log_activity("Button Clicked: Confirm")
        return res

    def action_cancel(self):
        res = super().action_cancel()
        self._log_activity("Button Clicked: Cancel")
        return res

    def action_draft(self):
        res = super().action_draft()
        self._log_activity("Button Clicked: Set to Quotation")
        return res

    def action_lock(self):
        res = super().action_lock()
        self._log_activity("Button Clicked: Lock")
        return res

    def action_unlock(self):
        res = super().action_unlock()
        self._log_activity("Button Clicked: Unlock")
        return res

    def action_quotation_send(self):
        res = super().action_quotation_send()
        self._log_activity("Button Clicked: Send by Email")
        return res
