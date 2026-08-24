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
# Câmpurile x2many (operațiile transferului) sunt descrise linie cu linie, deci
# au nevoie de un plafon mai larg — altfel s-ar pierde tocmai informația utilă.
MAX_RELATION_LENGTH = 2000
MAX_MESSAGE_LENGTH = 2000
MAX_LOG_LENGTH = 65536


def truncate(value, limit):
    """Scurtează ``value`` la ``limit`` caractere, marcând cât s-a tăiat."""
    if len(value) <= limit:
        return value
    return f"{value[:limit]}… (+{len(value) - limit} chars)"


def format_record_ref(model, value):
    """Nume lizibil pentru o valoare relațională: recordset, id sau id virtual.

    Valorile scrise nu sunt întotdeauna id-uri din baza de date: clientul web
    referă liniile încă nesalvate prin id-uri virtuale (``"virtual_7149"``), pe
    care le poate trimite atât în comenzile x2many, cât și într-un many2one. Un
    ``browse`` pe un id nenumeric ar produce un recordset cu un id per caracter,
    iar citirea lui ar arunca ``Expected singleton`` — de aceea afișăm id-ul așa
    cum a venit. Aceeași cale acoperă și o linie ștearsă între timp.
    """
    if isinstance(value, models.Model):
        return value.display_name or f"ID {value.id}"
    if model is None or not isinstance(value, int):
        return f"ID {value}"
    record = model.browse(value).exists()
    return record.display_name if record else f"ID {value}"


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _log_picking_activity_report(self, log_msg):
        try:
            if self.env.user.has_group("base.group_user") and self.env.user.login != "__system__":
                today = datetime.now().date()
                now = datetime.now().strftime("%H:%M:%S")
                full_log_msg = f"{now} - {truncate(log_msg, MAX_MESSAGE_LENGTH)}\n"
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
                        if self.env.context.get("awb_generated", False):
                            vals.update({"awb_generated": True})
                        self.env["stock.picking.activity.record"].sudo().create(vals)
                    else:
                        new_log = (existing_record.activity_log or "") + full_log_msg
                        if len(new_log) > MAX_LOG_LENGTH:
                            # Păstrăm coada (activitatea recentă) și tăiem de la
                            # prima linie completă, ca jurnalul să rămână lizibil.
                            new_log = new_log[-MAX_LOG_LENGTH:].split("\n", 1)[-1]
                        vals["activity_log"] = new_log
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
                        if self.env.context.get("awb_generated", False):
                            vals.update({"awb_generated": True})
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
                        if field_type in SKIPPED_FIELD_TYPES:
                            # Ieșim înainte de a citi valoarea veche: pentru un câmp
                            # binar, `picking[field_name]` ar încărca degeaba din
                            # filestore un conținut pe care oricum nu-l jurnalizăm.
                            continue
                        old_val = picking[field_name]
                        if field_name == "carrier_tracking_ref" and new_val is not False:
                            log_context["awb_generated"] = True

                        def format_val(val, f_type, f_name):
                            if not val:
                                return "None"
                            if f_type == "many2one":
                                relation = fields_info[f_name].get("relation")
                                return format_record_ref(self.env[relation] if relation else None, val)
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
                                        relation = target_fields_info[sub_f_name].get("relation")
                                        return format_record_ref(self.env[relation] if relation else None, sub_val)
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
                                        data = command[2]
                                        name_part = format_record_ref(target_model, command[1])
                                        readable_data = []
                                        for fname, fval in data.items():
                                            f_info = target_fields_info.get(fname, {})
                                            flabel = f_info.get("string", fname)
                                            f_type = f_info.get("type")
                                            readable_data.append(f"{flabel}: {format_sub_val(fval, f_type, fname)}")
                                        formatted_commands.append(f"Update {name_part}: [{', '.join(readable_data)}]")
                                    elif cmd_type == 2:  # DELETE
                                        name_part = format_record_ref(target_model, command[1])
                                        formatted_commands.append(f"Delete {name_part}")
                                    elif cmd_type == 3:  # UNLINK
                                        name_part = format_record_ref(target_model, command[1])
                                        formatted_commands.append(f"Remove {name_part}")
                                    elif cmd_type == 4:  # LINK
                                        name_part = format_record_ref(target_model, command[1])
                                        formatted_commands.append(f"Link {name_part}")
                                    elif cmd_type == 5:  # UNLINK ALL
                                        formatted_commands.append("Remove all")
                                    elif cmd_type == 6:  # REPLACE ALL
                                        formatted_commands.append(f"Replace all with IDs {command[2]}")
                                return " | ".join(formatted_commands) if formatted_commands else str(val)

                            return str(val)

                        limit = MAX_RELATION_LENGTH if field_type in ("one2many", "many2many") else MAX_VALUE_LENGTH
                        old_val_str = truncate(format_val(old_val, field_type, field_name), limit)
                        new_val_str = truncate(format_val(new_val, field_type, field_name), limit)

                        if old_val_str != new_val_str:
                            changes.append(f"{field_label}: {old_val_str} -> {new_val_str}")

                    if changes:
                        picking.with_context(**log_context)._log_picking_activity_report(
                            "Updated: " + ", ".join(changes)
                        )
        except Exception:
            _logger.exception("Error while logging activity in write")

        return super().write(vals)

    def message_post(self, **kwargs):
        res = super().message_post(**kwargs)
        body = kwargs.get("body", "")
        if body:
            clean_body = re.sub("<.*?>", "", body)
            if clean_body.strip():
                self.with_context(chatter_message=True)._log_picking_activity_report(f"Message: {clean_body.strip()}")
        return res

    def action_confirm(self):
        res = super().action_confirm()
        self._log_picking_activity_report("Button Clicked: Confirm")
        return res

    def action_assign(self):
        res = super().action_assign()
        self._log_picking_activity_report("Button Clicked: Check Availability")
        return res

    def button_validate(self):
        res = super().button_validate()
        for picking in self:
            counted_product_number = 0
            log_context = {"has_validated": True}
            for line in picking.move_ids:
                counted_product_number += line.quantity
            if picking.picking_type_id.code == "outgoing":
                log_context["exit_product_number"] = counted_product_number
                self.with_context(**log_context)._log_picking_activity_report("Button Clicked: Validate")
            if picking.picking_type_id.code == "incoming":
                log_context["entry_product_number"] = counted_product_number
                self.with_context(**log_context)._log_picking_activity_report("Button Clicked: Validate")
            if picking.picking_type_id.code == "internal":
                log_context["internal_product_number"] = counted_product_number
                self.with_context(**log_context)._log_picking_activity_report("Button Clicked: Validate")
        return res

    def action_cancel(self):
        res = super().action_cancel()
        self._log_picking_activity_report("Button Clicked: Cancel")
        return res
