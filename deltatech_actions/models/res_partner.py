import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResPartnerMergeCron(models.Model):
    _inherit = "res.partner"

    def _cron_merge_duplicate_contacts(self, limit=5):
        MergeWizard = self.env["base.partner.merge.automatic.wizard"]
        need_retrigger = False
        # Găsește grupuri de persoane duplicate după email
        self.env.cr.execute(
            """
            SELECT email, array_agg(id) AS partner_ids
            FROM res_partner
            WHERE email IS NOT NULL AND email != ''
              AND is_company = FALSE
                AND vat IS NULL
            GROUP BY email
            HAVING count(*) > 1
            LIMIT %s
        """,
            (limit+1,),
        )
        duplicates = self.env.cr.fetchall()
        if len(duplicates) > limit:
            duplicates = duplicates[:limit]
            need_retrigger = True

        for email, ids in duplicates:
            partners = self.env["res.partner"].browse(ids).exists()
            if len(partners) <= 1:
                continue
            partners.write({"parent_id": False})
            main = partners[0]  # îl păstrăm ca principal
            secundar = partners[1]
            _logger.info("Contactul %s a fost unit cu %s (Email: %s)", main.display_name, secundar.display_name, email)
            wizard = MergeWizard.create(
                {
                    "partner_ids": [(6, 0, [main.id, secundar.id])],
                }
            )
            wizard.action_merge()

        if need_retrigger:
            self.env.ref("deltatech_actions.ir_cron_merge_contacts")._trigger()


    def _cron_merge_duplicate_companies(self, limit=5):
        MergeWizard = self.env["base.partner.merge.automatic.wizard"]
        need_retrigger = False
        # Găsește grupuri de companii duplicate după CUI
        self.env.cr.execute(
            """
            SELECT vat, array_agg(id) AS partner_ids
            FROM res_partner
            WHERE vat IS NOT NULL
              AND vat != ''
              AND active = TRUE
              AND is_company = TRUE
              AND parent_id IS NULL
            GROUP BY vat
            HAVING count(*) > 1
            LIMIT %s
        """,
            (limit+1,),
        )
        duplicates = self.env.cr.fetchall()
        if len(duplicates) > limit:
            duplicates = duplicates[:limit]
            need_retrigger = True

        for _vat, ids in duplicates:
            partners = self.env["res.partner"].browse(ids).exists()
            if len(partners) <= 1:
                continue

            main = partners[0]  # păstrăm prima companie ca principală
            secundar = partners[1]

            _logger.info("Compania %s a fost unită cu %s (CUI: %s)", secundar.display_name, main.display_name, main.vat)
            wizard = MergeWizard.create(
                {
                    "partner_ids": [(6, 0, [main.id, secundar.id])],
                }
            )
            wizard.action_merge()

        if need_retrigger:
            self.env.ref("deltatech_actions.ir_cron_merge_companies")._trigger()
