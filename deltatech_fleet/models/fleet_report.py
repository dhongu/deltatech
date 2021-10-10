# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from psycopg2 import sql

from odoo import fields, models, tools


class FleetReport(models.Model):
    _inherit = "fleet.vehicle.cost.report"

    cost_type = fields.Selection(selection_add=[("fuel", "Fuel")], default="service", ondelete={"fuel": "set default"})
    cost_type_id = fields.Many2one("fleet.service.type", "Service Type", readonly=True)

    def init(self):
        query = """
WITH service_costs AS (
    SELECT
        ve.id AS vehicle_id,
        ve.company_id AS company_id,
        ve.name AS name,
        ve.driver_id AS driver_id,
        ve.fuel_type AS fuel_type,
        date(date_trunc('month', d)) AS date_start,
        COALESCE(sum(se.amount), 0) AS
        COST,
        'service' AS cost_type,
        se.service_type_id as cost_type_id
    FROM
        fleet_vehicle ve
    CROSS JOIN generate_series((
            SELECT
                min(date)
                FROM fleet_vehicle_log_services), CURRENT_DATE + '1 month'::interval, '1 month') d
        LEFT JOIN fleet_vehicle_log_services se ON se.vehicle_id = ve.id
            AND date_trunc('month', se.date) = date_trunc('month', d)
    WHERE
        ve.active AND se.active AND se.state != 'cancelled'
    GROUP BY
        ve.id,
        ve.company_id,
        ve.name,
        date_start,
        d,
        service_type_id
    ORDER BY
        ve.id,
        date_start
),
contract_costs AS (
    SELECT
        ve.id AS vehicle_id,
        ve.company_id AS company_id,
        ve.name AS name,
        ve.driver_id AS driver_id,
        ve.fuel_type AS fuel_type,
        date(date_trunc('month', d)) AS date_start,
        (COALESCE(sum(co.amount), 0) +
        COALESCE(sum(cod.cost_generated *
        extract(day FROM least (date_trunc('month', d) + interval '1 month', cod.expiration_date) -
         greatest (date_trunc('month', d), cod.start_date))), 0)
         + COALESCE(sum(com.cost_generated), 0) + COALESCE(sum(coy.cost_generated), 0)) AS COST,
        'contract' AS cost_type,
        COALESCE(co.cost_subtype_id, cod.cost_subtype_id, com.cost_subtype_id, coy.cost_subtype_id ) as cost_type_id
    FROM
        fleet_vehicle ve
    CROSS JOIN generate_series((
            SELECT
                min(acquisition_date)
                FROM fleet_vehicle), CURRENT_DATE + '1 month'::interval, '1 month') d
        LEFT JOIN fleet_vehicle_log_contract co ON co.vehicle_id = ve.id
            AND date_trunc('month', co.date) = date_trunc('month', d)
        LEFT JOIN fleet_vehicle_log_contract cod ON cod.vehicle_id = ve.id
            AND date_trunc('month', cod.start_date) <= date_trunc('month', d)
            AND date_trunc('month', cod.expiration_date) >= date_trunc('month', d)
            AND cod.cost_frequency = 'daily'
    LEFT JOIN fleet_vehicle_log_contract com ON com.vehicle_id = ve.id
        AND date_trunc('month', com.start_date) <= date_trunc('month', d)
        AND date_trunc('month', com.expiration_date) >= date_trunc('month', d)
        AND com.cost_frequency = 'monthly'
    LEFT JOIN fleet_vehicle_log_contract coy ON coy.vehicle_id = ve.id
        AND date_trunc('month', coy.date) = date_trunc('month', d)
        AND date_trunc('month', coy.start_date) <= date_trunc('month', d)
        AND date_trunc('month', coy.expiration_date) >= date_trunc('month', d)
        AND coy.cost_frequency = 'yearly'
WHERE
    ve.active
GROUP BY
    ve.id,
    ve.company_id,
    ve.name,
    date_start,
    d,
    co.cost_subtype_id, cod.cost_subtype_id, com.cost_subtype_id, coy.cost_subtype_id
ORDER BY
    ve.id,
    date_start
)
SELECT
    vehicle_id AS id,
    company_id,
    vehicle_id,
    name,
    driver_id,
    fuel_type,
    date_start,
    COST,
    'service' as cost_type,
    sc.cost_type_id,
    0 as distance,
    0 as price
FROM
    service_costs sc
UNION ALL (
    SELECT
        vehicle_id AS id,
        company_id,
        vehicle_id,
        name,
        driver_id,
        fuel_type,
        date_start,
        COST,
        'contract' as cost_type,
        cc.cost_type_id,
        0 as distance,
        0 as price
    FROM
        contract_costs cc)
"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            sql.SQL("""CREATE or REPLACE VIEW {} as ({})""").format(sql.Identifier(self._table), sql.SQL(query))
        )
