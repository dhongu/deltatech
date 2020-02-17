# -*- coding: utf-8 -*-
#
# ©  2013 Vauxoo (info@vauxoo.com)
#              Sabrina Romero (sabrina@vauxoo.com)
# ©  2019 Deltatech
#              Dorin Hongu (dhongu@gmail.com)
#
# See README.rst file on addons root folder for license details




from __future__ import absolute_import
from ast import literal_eval
import functools
import itertools
import logging
import psycopg2

from odoo import api, fields, models, _
from odoo import SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import mute_logger



_logger = logging.getLogger('base.product.merge')


def is_integer_list(ids):
    return all(isinstance(i, (int)) for i in ids)


class MergeProductLine(models.TransientModel):
    _name = 'base.product.merge.line'
    _description = 'MergeProductLine'
    _order = 'min_id asc'

    wizard_id = fields.Many2one(         'base.product.merge.automatic.wizard',         'Wizard')
    min_id = fields.Integer('MinID')
    aggr_ids = fields.Char('Ids', required=True)


class MergeProductAutomatic(models.TransientModel):
    _name = 'base.product.merge.automatic.wizard'
    _description =  'MergeProductAutomatic'

    group_by_product_tmpl_id = fields.Boolean('Template')
    group_by_default_code = fields.Boolean('Reference')
    group_by_categ_id = fields.Boolean('Category')
    group_by_uom_id = fields.Boolean('Unit of measure')
    state = fields.Selection(
        [('option', 'Option'),
         ('selection', 'Selection'),
         ('finished', 'Finished')],
        'State', readonly=True, default='option', required=True
    )
    number_group = fields.Integer("Group of Products", readonly=True)
    current_product_id = fields.Many2one('product.product', string='Current product')
    product_from = fields.Many2one('product.product', string='Product from')
    product_to = fields.Many2one('product.product', string='Product to')
    current_line_id = fields.Many2one('base.product.merge.line', 'Current Line')
    line_ids = fields.One2many('base.product.merge.line', 'wizard_id', 'Lines')
    dst_product_id = fields.Many2one('product.product', string='Destination Contact')
    product_ids = fields.Many2many(
        'product.product', 'product_rel', 'product_merge_id',
        'product_id', string="Products to merge"
    )
    maximum_group = fields.Integer("Maximum of Group of Products")
    exclude_journal_item = fields.Boolean('Journal Items associated to the product')



    @api.model
    def default_get(self, fields):
        res = super(MergeProductAutomatic, self).default_get(fields)
        active_ids = self.env.context.get('active_ids')
        if self.env.context.get('active_model') == 'product.product' and active_ids:
            res['state'] = 'selection'
            res['product_ids'] = active_ids
            res['dst_product_id'] = self._get_ordered_product(active_ids)[-1].id
        if self.env.context.get('active_model') == 'product.template' and active_ids:
            templates = self.env['product.template'].browse(active_ids)
            active_ids = []
            for template in templates:
                active_ids += template.product_variant_ids.ids
            res['state'] = 'selection'
            res['product_ids'] = active_ids
            res['dst_product_id'] = self._get_ordered_product(active_ids)[-1].id
        return res

    # ----------------------------------------
    # Update method. Core methods to merge steps
    # ----------------------------------------


    def _get_fk_on(self, table):
        """ return a list of many2one relation with the given table.
            :param table : the name of the sql table to return relations
            :returns a list of tuple 'table name', 'column name'.
        """
        query = """
            SELECT cl1.relname as table, att1.attname as column
            FROM pg_constraint as con, pg_class as cl1, pg_class as cl2, pg_attribute as att1, pg_attribute as att2
            WHERE con.conrelid = cl1.oid
                AND con.confrelid = cl2.oid
                AND array_lower(con.conkey, 1) = 1
                AND con.conkey[1] = att1.attnum
                AND att1.attrelid = cl1.oid
                AND cl2.relname = %s
                AND att2.attname = 'id'
                AND array_lower(con.confkey, 1) = 1
                AND con.confkey[1] = att2.attnum
                AND att2.attrelid = cl2.oid
                AND con.contype = 'f'
        """
        self._cr.execute(query, (table,))
        return self._cr.fetchall()

    @api.model
    def _update_foreign_keys(self, src_products, dst_product):
        """ Update all foreign key from the src_products to dst_product. All many2one fields will be updated.
            :param src_products : merge source product.product recordset (does not include destination one)
            :param dst_product : record of destination product.product
        """
        _logger.debug('_update_foreign_keys for dst_product: %s for src_products: %s', dst_product.id,
                      str(src_products.ids))

        # find the many2one relation to a product
        Product = self.env['product.product']
        relations = self._get_fk_on('product_product')

        for table, column in relations:
            if 'base_product_merge_' in table:  # ignore two tables
                continue

            # get list of columns of current table (exept the current fk column)
            query = "SELECT column_name FROM information_schema.columns WHERE table_name LIKE '%s'" % (table)
            self._cr.execute(query, ())
            columns = []
            for data in self._cr.fetchall():
                if data[0] != column:
                    columns.append(data[0])

            # do the update for the current table/column in SQL
            query_dic = {
                'table': table,
                'column': column,
                'value': columns[0],
            }
            if len(columns) <= 1:
                # unique key treated
                query = """
                    UPDATE "%(table)s" as ___tu
                    SET "%(column)s" = %%s
                    WHERE
                        "%(column)s" = %%s AND
                        NOT EXISTS (
                            SELECT 1
                            FROM "%(table)s" as ___tw
                            WHERE
                                "%(column)s" = %%s AND
                                ___tu.%(value)s = ___tw.%(value)s
                        )""" % query_dic
                for product in src_products:
                    self._cr.execute(query, (dst_product.id, product.id, dst_product.id))
            else:
                try:
                    with mute_logger('odoo.sql_db'), self._cr.savepoint():
                        query = 'UPDATE "%(table)s" SET "%(column)s" = %%s WHERE "%(column)s" IN %%s' % query_dic
                        self._cr.execute(query, (dst_product.id, tuple(src_products.ids),))


                except psycopg2.Error:
                    # updating fails, most likely due to a violated unique constraint
                    # keeping record with nonexistent product_id is useless, better delete it
                    query = 'DELETE FROM "%(table)s" WHERE "%(column)s" IN %%s' % query_dic
                    self._cr.execute(query, (tuple(src_products.ids),))

    @api.model
    def _update_reference_fields(self, src_products, dst_product):
        """ Update all reference fields from the src_products to dst_product.
            :param src_products : merge source product.product recordset (does not include destination one)
            :param dst_product : record of destination product.product
        """
        _logger.debug('_update_reference_fields for dst_product: %s for src_products: %r', dst_product.id,
                      src_products.ids)

        def update_records(model, src, field_model='model', field_id='res_id'):
            Model = self.env[model] if model in self.env else None
            if Model is None:
                return
            records = Model.sudo().search([(field_model, '=', 'product.product'), (field_id, '=', src.id)])
            try:
                with mute_logger('odoo.sql_db'), self._cr.savepoint():
                    return records.sudo().write({field_id: dst_product.id})
            except psycopg2.Error:
                # updating fails, most likely due to a violated unique constraint
                # keeping record with nonexistent product_id is useless, better delete it
                return records.sudo().unlink()

        update_records = functools.partial(update_records)

        for product in src_products:
            update_records('ir.attachment', src=product, field_model='res_model')
            update_records('mail.followers', src=product, field_model='res_model')
            update_records('mail.message', src=product)
            update_records('ir.model.data', src=product)

        records = self.env['ir.model.fields'].search([('ttype', '=', 'reference')])
        for record in records.sudo():
            try:
                Model = self.env[record.model]
                field = Model._fields[record.name]
            except KeyError:
                # unknown model or field => skip
                continue

            if field.compute is not None:
                continue

            for product in src_products:
                records_ref = Model.sudo().search([(record.name, '=', 'product.product,%d' % product.id)])
                values = {
                    record.name: 'product.product,%d' % dst_product.id,
                }
                records_ref.sudo().write(values)

    @api.model
    def _update_values(self, src_products, dst_product):
        """ Update values of dst_product with the ones from the src_products.
            :param src_products : recordset of source product.product
            :param dst_product : record of destination product.product
        """
        _logger.debug('_update_values for dst_product: %s for src_products: %r', dst_product.id, src_products.ids)

        model_fields = dst_product.fields_get().keys()

        def write_serializer(item):
            if isinstance(item, models.BaseModel):
                return item.id
            else:
                return item

        # get all fields that are not computed or x2many
        values = dict()
        for column in model_fields:
            field = dst_product._fields[column]
            if field.type not in ('many2many', 'one2many') and field.compute is None:
                for item in itertools.chain(src_products, [dst_product]):
                    if item[column]:
                        values[column] = write_serializer(item[column])
        # remove fields that can not be updated (id and parent_id)
        values.pop('id', None)
        parent_id = values.pop('parent_id', None)
        dst_product.write(values)
        # try to update the parent_id
        if parent_id and parent_id != dst_product.id:
            try:
                dst_product.write({'parent_id': parent_id})
            except ValidationError:
                _logger.info('Skip recursive product hierarchies for parent_id %s of product: %s', parent_id,
                             dst_product.id)

    def _merge(self, product_ids, dst_product=None):
        """ private implementation of merge product
            :param product_ids : ids of product to merge
            :param dst_product : record of destination product.product
        """
        Product = self.env['product.product']
        product_ids = Product.browse(product_ids).exists()
        if len(product_ids) < 2:
            return

        if len(product_ids) > 3:
            raise UserError(_(
                "For safety reasons, you cannot merge more than 3 product together. You can re-open the wizard several times if needed."))

        # remove dst_product from products to merge
        if dst_product and dst_product in product_ids:
            src_products = product_ids - dst_product
        else:
            ordered_products = self._get_ordered_product(product_ids.ids)
            dst_product = ordered_products[-1]
            src_products = ordered_products[:-1]
        _logger.info("dst_product: %s", dst_product.id)

        # FIXME: is it still required to make and exception for account.move.line since accounting v9.0 ?
        if SUPERUSER_ID != self.env.uid and 'account.move.line' in self.env and self.env[
            'account.move.line'].sudo().search([('product_id', 'in', [product.id for product in src_products])]):
            raise UserError(_(
                "Only the destination contact may be linked to existing Journal Items. Please ask the Administrator if you need to merge several contacts linked to existing Journal Items."))

        # call sub methods to do the merge
        self._update_foreign_keys(src_products, dst_product)
        self._update_reference_fields(src_products, dst_product)
        self._update_values(src_products, dst_product)

        _logger.info('(uid = %s) merged the products %r with %s', self._uid, src_products.ids, dst_product.id)
        dst_product.message_post(body='%s %s' % (_("Merged with the following products:"), ", ".join(
            '%s  (ID %s)' % (p.name,  p.id) for p in src_products)))

        # delete source product, since they are merged
        src_products.unlink()

        # ----------------------------------------
        # Helpers
        # ----------------------------------------

    @api.model
    def _generate_query(self, fields, maximum_group=100):
        """ Build the SQL query on product.product table to group them according to given criteria
            :param fields : list of column names to group by the products
            :param maximum_group : limit of the query
        """
        # make the list of column to group by in sql query
        sql_fields = []
        for field in fields:
            if field in ['email', 'name']:
                sql_fields.append('lower(%s)' % field)
            elif field in ['vat']:
                sql_fields.append("replace(%s, ' ', '')" % field)
            else:
                sql_fields.append(field)
        group_fields = ', '.join(sql_fields)

        # where clause : for given group by columns, only keep the 'not null' record
        filters = []
        for field in fields:
            if field in ['email', 'name', 'vat']:
                filters.append((field, 'IS NOT', 'NULL'))
        criteria = ' AND '.join('%s %s %s' % (field, operator, value) for field, operator, value in filters)

        # build the query
        text = [
            "SELECT min(id), array_agg(id)",
            "FROM product_product",
        ]

        if criteria:
            text.append('WHERE %s' % criteria)

        text.extend([
            "GROUP BY %s" % group_fields,
            "HAVING COUNT(*) >= 2",
            "ORDER BY min(id)",
        ])

        if maximum_group:
            text.append("LIMIT %s" % maximum_group, )

        return ' '.join(text)

    @api.model
    def _compute_selected_groupby(self):
        """ Returns the list of field names the product can be grouped (as merge
            criteria) according to the option checked on the wizard
        """
        groups = []
        group_by_prefix = 'group_by_'

        for field_name in self._fields:
            if field_name.startswith(group_by_prefix):
                if getattr(self, field_name, False):
                    groups.append(field_name[len(group_by_prefix):])

        if not groups:
            raise UserError(_("You have to specify a filter for your selection"))

        return groups

    # ----------------------------------------
    # Helpers
    # ----------------------------------------

    @api.model
    def _generate_query(self, fields, maximum_group=100):
        """ Build the SQL query on product.producttable to group them according to given criteria
            :param fields : list of column names to group by the products
            :param maximum_group : limit of the query
        """
        # make the list of column to group by in sql query
        sql_fields = []
        for field in fields:
            if field in ['default_code', 'name']:
                sql_fields.append('lower(%s)' % field)
            else:
                sql_fields.append(field)
        group_fields = ', '.join(sql_fields)

        # where clause : for given group by columns, only keep the 'not null' record
        filters = []
        for field in fields:
            if field in ['default_code', 'name']:
                filters.append((field, 'IS NOT', 'NULL'))
        criteria = ' AND '.join('%s %s %s' % (field, operator, value) for field, operator, value in filters)

        # build the query
        text = [
            "SELECT min(id), array_agg(id)",
            "FROM product_product",
        ]

        if criteria:
            text.append('WHERE %s' % criteria)

        text.extend([
            "GROUP BY %s" % group_fields,
            "HAVING COUNT(*) >= 2",
            "ORDER BY min(id)",
        ])

        if maximum_group:
            text.append("LIMIT %s" % maximum_group, )

        return ' '.join(text)

    @api.model
    def _compute_selected_groupby(self):
        """ Returns the list of field names the product can be grouped (as merge
            criteria) according to the option checked on the wizard
        """
        groups = []
        group_by_prefix = 'group_by_'

        for field_name in self._fields:
            if field_name.startswith(group_by_prefix):
                if getattr(self, field_name, False):
                    groups.append(field_name[len(group_by_prefix):])

        if not groups:
            raise UserError(_("You have to specify a filter for your selection"))

        return groups

    @api.model
    def _product_use_in(self, aggr_ids, models):
        """ Check if there is no occurence of this group of product in the selected model
            :param aggr_ids : stringified list of product ids separated with a comma (sql array_agg)
            :param models : dict mapping a model name with its foreign key with product_product table
        """
        return any(
            self.env[model].search_count([(field, 'in', aggr_ids)])
            for model, field in models.items()
        )

    @api.model
    def _get_ordered_product(self, product_ids):
        """ Helper : returns a `product.product` recordset ordered by create_date/active fields
            :param product_ids : list of product ids to sort
        """
        return self.env['product.product'].browse(product_ids).sorted(
            key=lambda p: (p.active, (p.create_date or '')),
            reverse=True,
        )


    def _compute_models(self):
        """ Compute the different models needed by the system if you want to exclude some products. """
        model_mapping = {}

        if 'account.move.line' in self.env and self.exclude_journal_item:
            model_mapping['account.move.line'] = 'product_id'
        return model_mapping

    # ----------------------------------------
    # Actions
    # ----------------------------------------


    def action_skip(self):
        """ Skip this wizard line. Don't compute any thing, and simply redirect to the new step."""
        if self.current_line_id:
            self.current_line_id.unlink()
        return self._action_next_screen()


    def _action_next_screen(self):
        """ return the action of the next screen ; this means the wizard is set to treat the
            next wizard line. Each line is a subset of product that can be merged together.
            If no line left, the end screen will be displayed (but an action is still returned).
        """
        self.invalidate_cache()  # FIXME: is this still necessary?
        values = {}
        if self.line_ids:
            # in this case, we try to find the next record.
            current_line = self.line_ids[0]
            current_product_ids = literal_eval(current_line.aggr_ids)
            values.update({
                'current_line_id': current_line.id,
                'product_ids': [(6, 0, current_product_ids)],
                'dst_product_id': self._get_ordered_product(current_product_ids)[-1].id,
                'state': 'selection',
            })
        else:
            values.update({
                'current_line_id': False,
                'product_ids': [],
                'state': 'finished',
            })

        self.write(values)

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


    def _process_query(self, query):
        """ Execute the select request and write the result in this wizard
            :param query : the SQL query used to fill the wizard line
        """
        self.ensure_one()
        model_mapping = self._compute_models()

        # group product query
        self._cr.execute(query)

        counter = 0
        for min_id, aggr_ids in self._cr.fetchall():
            # To ensure that the used products are accessible by the user
            products = self.env['product.product'].search([('id', 'in', aggr_ids)])
            if len(products) < 2:
                continue

            # exclude product according to options
            if model_mapping and self._product_use_in(products.ids, model_mapping):
                continue

            self.env['base.product.merge.line'].create({
                'wizard_id': self.id,
                'min_id': min_id,
                'aggr_ids': products.ids,
            })
            counter += 1

        self.write({
            'state': 'selection',
            'number_group': counter,
        })

        _logger.info("counter: %s", counter)


    def action_start_manual_process(self):
        """ Start the process 'Merge with Manual Check'. Fill the wizard according to the group_by and exclude
            options, and redirect to the first step (treatment of first wizard line). After, for each subset of
            product to merge, the wizard will be actualized.
                - Compute the selected groups (with duplication)
                - If the user has selected the 'exclude_xxx' fields, avoid the products
        """
        self.ensure_one()
        groups = self._compute_selected_groupby()
        query = self._generate_query(groups, self.maximum_group)
        self._process_query(query)
        return self._action_next_screen()


    def action_start_automatic_process(self):
        """ Start the process 'Merge Automatically'. This will fill the wizard with the same mechanism as 'Merge
            with Manual Check', but instead of refreshing wizard with the current line, it will automatically process
            all lines by merging product grouped according to the checked options.
        """
        self.ensure_one()
        self.action_start_manual_process()  # here we don't redirect to the next screen, since it is automatic process
        self.invalidate_cache()  # FIXME: is this still necessary?

        for line in self.line_ids:
            product_ids = literal_eval(line.aggr_ids)
            self._merge(product_ids)
            line.unlink()
            self._cr.commit()  # TODO JEM : explain why

        self.write({'state': 'finished'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


    def action_merge(self):
        """ Merge Product button. Merge the selected products, and redirect to
            the end screen (since there is no other wizard line to process.
        """
        if not self.product_ids:
            self.write({'state': 'finished'})
            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }

        self._merge(self.product_ids.ids, self.dst_product_id)

        if self.current_line_id:
            self.current_line_id.unlink()

        return self._action_next_screen()
