# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResPartnerMergeCron(models.Model):
    _inherit = "res.partner"

    def _compute_vies_valid(self):
        if self.env.context.get("skip_vies_check"):
            return
        return super()._compute_vies_valid()

    def _cron_merge_duplicate_contacts(self, limit=10):
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
            (limit + 1,),
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

    def _cron_merge_duplicate_companies(self, limit=10):
        MergeWizard = self.env["base.partner.merge.automatic.wizard"].with_context(skip_vies_check=True)
        need_retrigger = False
        # Găsește grupuri de companii duplicate după CUI
        self.env.cr.execute(
            """
            SELECT vat, array_agg(id) AS partner_ids
            FROM res_partner
            WHERE vat IS NOT NULL
              AND vat not in  ('','0','-')
              AND active = TRUE
              AND is_company = TRUE
              AND parent_id IS NULL
            GROUP BY vat
            HAVING count(*) > 1
            LIMIT %s
        """,
            (limit + 1,),
        )
        duplicates = self.env.cr.fetchall()
        if len(duplicates) > limit:
            duplicates = duplicates[:limit]
            need_retrigger = True

        for _vat, ids in duplicates:
            partners = self.env["res.partner"].browse(ids).exists()
            if len(partners) <= 1:
                continue
            partners = partners.with_context(skip_vies_check=True)
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

    def batch_normalize_company_names(self, batch_size=1000):
        """Normalizează numele companiilor în loturi pentru performanță"""

        # Găsește toate companiile care au nevoie de normalizare
        query_count = r"""
              SELECT COUNT(*)
              FROM res_partner
              WHERE is_company = true
                AND (
                    name ~* '.*\s+srl\s*$' OR
                    name ~* '.*\s+s\.?\s*r\.?\s*l\.?\s*$' OR
                    name ~* '.*\s+sa\s*$' OR
                    name ~* '.*\s+s\.?\s*a\.?\s*$' OR
                    name ~* '.*\s+pfa\s*$' OR
                    name ~* '.*\s+ii\s*$'
                  )
              """

        self.env.cr.execute(query_count)
        total_companies = self.env.cr.fetchone()[0]

        if total_companies == 0:
            _logger.info("Nu sunt companii care să necesite normalizare")
            return 0

        offset = 0
        total_updated = 0

        # noqa: W1401
        query_update = r"""
           UPDATE res_partner
           SET name = CASE
                          WHEN name ~* '.*\s+srl\s*$' THEN REGEXP_REPLACE(name, '\s+srl\s*$', ' S.R.L.', 'i')
                          WHEN name ~* '.*\s+s\.?\s*r\.?\s*l\.?\s*$' THEN REGEXP_REPLACE(name, '\s+s\.?\s*r\.?\s*l\.?\s*$', ' S.R.L.', 'i')
                          WHEN name ~* '.*\s+sa\s*$' THEN REGEXP_REPLACE(name, '\s+sa\s*$', ' S.A.', 'i')
                          WHEN name ~* '.*\s+s\.?\s*a\.?\s*$' THEN REGEXP_REPLACE(name, '\s+s\.?\s*a\.?\s*$', ' S.A.', 'i')
                          WHEN name ~* '.*\s+pfa\s*$' THEN REGEXP_REPLACE(name, '\s+pfa\s*$', ' P.F.A.', 'i')
                          WHEN name ~* '.*\s+ii\s*$' THEN REGEXP_REPLACE(name, '\s+ii\s*$', ' I.I.', 'i')
                          ELSE name
               END
           WHERE id IN (SELECT id
                        FROM res_partner
                        WHERE is_company = true
                          AND (
                            name ~* '.*\s+srl\s*$' OR
                            name ~* '.*\s+s\.?\s*r\.?\s*l\.?\s*$' OR
                            name ~* '.*\s+sa\s*$' OR
                            name ~* '.*\s+s\.?\s*a\.?\s*$' OR
                            name ~* '.*\s+pfa\s*$' OR
                            name ~* '.*\s+ii\s*$'
                            )
                        ORDER BY id
               LIMIT %s
           OFFSET %s )
                       """

        try:
            self.env.cr.execute(query_update, [batch_size, offset])
            batch_updated = self.env.cr.rowcount
            total_updated += batch_updated

            _logger.info(
                f"Procesate {offset + batch_size}/{total_companies} companii, actualizate {batch_updated} în acest lot"
            )

        except Exception as e:
            _logger.error(f"Eroare la procesarea lotului {offset}-{offset + batch_size}: {e}")

        return total_updated

    @api.model
    def cron_normalize_company_names(self):
        """Cron job pentru normalizarea periodică a numelor de companii"""
        _logger.info("Începe normalizarea automată a numelor de companii")

        try:
            updated_count = self.batch_normalize_company_names(batch_size=500)

            # Creează un mesaj în log
            if updated_count > 0:
                message = self.env._("Cron job: Au fost normalizate %s nume de companii", updated_count)
                _logger.info(message)

                # Opțional: trimite notificare către administrator
                admin_users = self.env["res.users"].search([("group_ids", "in", self.env.ref("base.group_system").id)])
                if admin_users:
                    for admin in admin_users:
                        admin.partner_id.message_post(
                            body=message, subject=self.env._("Normalizare companii - Cron Job")
                        )
            else:
                _logger.info("Cron job: Nu au fost găsite companii care să necesite normalizare")

        except Exception as e:
            _logger.error(f"Eroare în cron job pentru normalizarea companiilor: {e}")

            # Notifică administratorul despre eroare
            admin_users = self.env["res.users"].search([("group_ids", "in", self.env.ref("base.group_system").id)])
            if admin_users:
                for admin in admin_users:
                    admin.partner_id.message_post(
                        body=self.env._("Eroare în normalizarea companiilor: %s", e),
                        subject=self.env._("EROARE - Normalizare companii - Cron Job"),
                    )
