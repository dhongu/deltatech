# Part of Terrabit. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

from ..utils.scan import history_needs_new_interval


class WebScanHistoryMixin(models.AbstractModel):
    """The history of what a page showed, as intervals: a new line only when one of the compared values
    changes (``_scan_history_keys``); a reading that finds the same values only extends the last line.

    The model that inherits it names the field of the source (``_scan_source_field``, a Many2one).
    """

    _name = "web.scan.history.mixin"
    _description = "Web Scan History"
    _order = "date_start desc, id desc"
    _scan_source_field = None
    _scan_history_keys = ()

    date_start = fields.Datetime(string="From", required=True, readonly=True, index=True)
    date_end = fields.Datetime(string="Last Seen", required=True, readonly=True)

    def _scan_history_values(self):
        """:return: the compared values of the line, the relations as ids"""
        self.ensure_one()
        values = {}
        for key in self._scan_history_keys:
            value = self[key]
            values[key] = value.id if isinstance(value, models.BaseModel) else value
        return values

    @api.model
    def _scan_record_interval(self, source, values, date=None):
        """Extend the last interval of the source, or open a new one when a compared value changed

        :param source: the record of the source (one)
        :param values: the values read, for the fields of the history model
        :return: the line of history extended or created
        """
        date = date or fields.Datetime.now()
        last = self.search([(self._scan_source_field, "=", source.id)], order="date_start desc, id desc", limit=1)
        if last and not history_needs_new_interval(last._scan_history_values(), values, self._scan_history_keys):
            last.date_end = date
            return last
        return self.create(dict(values, date_start=date, date_end=date, **{self._scan_source_field: source.id}))
