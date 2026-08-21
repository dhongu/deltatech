# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


class Website(models.Model):
    _inherit = "website"

    @api.depends("company_id.account_fiscal_country_id")
    def _compute_show_line_subtotals_tax_selection(self):
        """EXTENDS 'website_sale' - nu lasa recalculul sa stearga valoarea deja setata.

        `show_line_subtotals_tax_selection` e un camp calculat si stocat, fara
        override pentru Romania: la fiecare recalcul, `website_sale` il pune
        neconditionat pe 'tax_excluded'. Recalculul se declanseaza la orice scriere
        pe `company_id.account_fiscal_country_id`, care la randul lui depinde de
        adresa partenerului companiei (`res.company._compute_address`) - de exemplu
        cand un cron de sincronizare cu ANAF (vezi `l10n_ro_anaf_partner`) rescrie
        adresa propriului partener al companiei.

        Citim direct din DB (nu prin ORM): campul e in curs de calcul, asa ca o
        citire ORM ar re-declansa acelasi compute in loc sa dea ultima valoare
        salvata.
        """
        real_ids = [record.id for record in self if isinstance(record.id, int)]
        previous_values = {}
        if real_ids:
            # raw SQL nu vede scrierile ORM inca necomise in DB (write() le tine
            # doar in cache-ul ORM pana la un flush) - fortam flush-ul intai.
            self.env.flush_all()
            self.env.cr.execute(
                "SELECT id, show_line_subtotals_tax_selection FROM website WHERE id IN %s",
                (tuple(real_ids),),
            )
            previous_values = dict(self.env.cr.fetchall())

        super()._compute_show_line_subtotals_tax_selection()

        for website in self:
            previous_value = previous_values.get(website.id)
            if previous_value:
                website.show_line_subtotals_tax_selection = previous_value
