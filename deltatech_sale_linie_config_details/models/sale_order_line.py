# ©  2025 Terrabit
# See README.rst file on addons root folder for license details

import ast
import json

from markupsafe import Markup, escape

from odoo import fields, models

# Keys of a detail dictionary that are never shown as text.
HIDDEN_KEYS = {"id"}
# Keys of a detail dictionary shown as a picture, with the size of the thumbnail.
IMAGE_KEYS = {"image": 100, "src": 200}


def parse_config_details(value):
    """Return ``value`` as a Python structure.

    A text is read as JSON, then as a Python literal (the 19.0 field was a text and the importers
    wrote ``str()`` of a list in it). A text that is neither stays a text. Nothing is evaluated.
    """
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except ValueError:
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError, MemoryError, RecursionError):
            return value


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    config_details = fields.Json(
        string="Config Details",
        copy=True,
        help="Configuration of the line as a list of {'name': ..., 'value': ...}; "
        "the value is a text or a dictionary of texts (dictionaries can nest).",
    )

    def _get_config_details(self):
        """Return the details as a list of dictionaries (empty when none or malformed)."""
        self.ensure_one()
        details = parse_config_details(self.config_details)
        if isinstance(details, dict):
            details = [details]
        if not isinstance(details, list):
            return []
        return [item for item in details if isinstance(item, dict)]

    def get_images_config_detail(self):
        """Return the image URLs found in the details (``image`` keys of the dictionary values)."""
        self.ensure_one()
        images = []
        for item in self._get_config_details():
            value = item.get("value")
            if isinstance(value, dict):
                images += [str(val) for key, val in value.items() if key == "image" and val]
        return images

    def _config_details_html(self, items):
        """Render a dictionary of details: texts as ``key: value``, dictionaries as nested rows."""
        rows, images = [], []
        for key, val in items.items():
            if key in HIDDEN_KEYS:
                continue
            if key in IMAGE_KEYS and val:
                images.append(
                    Markup(
                        "<img src='{url}' width='{size}' height='{size}'/> <a href='{url}' target='_blank'>{label}</a>"
                    ).format(url=escape(val), size=IMAGE_KEYS[key], label=self.env._("Open image"))
                )
            elif isinstance(val, dict):
                rows.append(
                    Markup("<div class='col-2'>{key}</div><div class='col-10'>{inner}</div>").format(
                        key=escape(key), inner=self._config_details_html(val)
                    )
                )
            elif isinstance(val, str | int | float) and not isinstance(val, bool) and val != "":
                rows.append(
                    Markup("<div class='col-2'><span>{key}: {val}</span></div>").format(
                        key=escape(key), val=escape(val)
                    )
                )
        html = Markup("<div class='row'>") + Markup("").join(rows) + Markup("</div>")
        if images:
            html += Markup("<div class='row'><div class='col-12'>") + Markup(" ").join(images) + Markup("</div></div>")
        return html

    def get_html_config_details(self, with_attributes=False):
        """HTML of the details. Everything coming from the data is escaped.

        :param with_attributes: also show the groups whose value is a plain text
        """
        self.ensure_one()
        parts = []
        for item in self._get_config_details():
            if "name" not in item and "value" not in item:
                # a bare dictionary of details, without a group name
                parts.append(Markup("<div>{inner}</div>").format(inner=self._config_details_html(item)))
                continue
            name, value = item.get("name"), item.get("value")
            label = Markup("<strong>{name}:</strong> ").format(name=name) if name not in (None, "") else Markup("")
            if isinstance(value, str) and with_attributes:
                parts.append(Markup("<div>{label}{value}</div>").format(label=label, value=value))
            elif isinstance(value, dict):
                parts.append(
                    Markup("<div>{label}</div><div>{inner}</div>").format(
                        label=label, inner=self._config_details_html(value)
                    )
                )
        if not parts:
            return Markup("")
        return Markup("<div>") + Markup("").join(parts) + Markup("</div>")

    def action_open_config_details(self):
        self.ensure_one()
        wizard = self.env["sale.order.line.config.details"].create(
            {"config_details": self.get_html_config_details(with_attributes=True)}
        )
        return {
            "name": self.env._("Config Details"),
            "type": "ir.actions.act_window",
            "res_model": wizard._name,
            "view_mode": "form",
            "res_id": wizard.id,
            "target": "new",
        }
