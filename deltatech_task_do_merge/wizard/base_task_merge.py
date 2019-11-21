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

import operator
from odoo.osv.orm import browse_record

_logger = logging.getLogger('base.task.merge')


def is_integer_list(ids):
    return all(isinstance(i, (int)) for i in ids)


class MergeTaskLine(models.TransientModel):
    _name = 'base.task.merge.line'
    _description = 'MergeTaskLine'
    _order = 'min_id asc'

    wizard_id = fields.Many2one('base.task.merge.automatic.wizard', 'Wizard')
    min_id = fields.Integer('MinID')
    aggr_ids = fields.Char('Ids', required=True)


class MergeTaskAutomatic(models.TransientModel):
    _name = 'base.task.merge.automatic.wizard'
    _description = 'MergeTaskAutomatic'

    state = fields.Selection(
        [('option', 'Option'),
         ('selection', 'Selection'),
         ('finished', 'Finished')],
        'State', readonly=True, default='option', required=True
    )
    number_group = fields.Integer("Group of Tasks", readonly=True)
    current_task_id = fields.Many2one('project.task', string='Current task')

    task_from = fields.Many2one('project.task', string='Task from')

    task_to = fields.Many2one('project.task', string='Task to')

    current_line_id = fields.Many2one('base.task.merge.line', 'Current Line')
    line_ids = fields.One2many('base.task.merge.line', 'wizard_id', 'Lines')
    dst_task_id = fields.Many2one('project.task', string='Destination Task')
    task_ids = fields.Many2many(
        'project.task', 'task_rel', 'task_merge_id',
        'task_id', string="Tasks to merge"
    )
    maximum_group = fields.Integer("Maximum of Group of Tasks")
    exclude_journal_item = fields.Boolean('Journal Items associated to the task')

    @api.model
    def default_get(self, fields):
        res = super(MergeTaskAutomatic, self).default_get(fields)
        active_ids = self.env.context.get('active_ids')
        if self.env.context.get('active_model') == 'project.task' and active_ids:
            res['state'] = 'selection'
            res['task_ids'] = active_ids
            res['dst_task_id'] = self._get_ordered_task(active_ids)[-1].id
        # if self.env.context.get('active_model') == 'task.template' and active_ids:
        #     templates = self.env['task.template'].browse(active_ids)
        #     active_ids = []
        #     for template in templates:
        #         active_ids += template.task_variant_ids.ids
        #     res['state'] = 'selection'
        #     res['task_ids'] = active_ids
        #     res['dst_task_id'] = self._get_ordered_task(active_ids)[-1].id
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
    def _update_foreign_keys(self, src_tasks, dst_task):
        """ Update all foreign key from the src_tasks to dst_task. All many2one fields will be updated.
            :param src_tasks : merge source task.task recordset (does not include destination one)
            :param dst_task : record of destination task.task
        """
        _logger.debug('_update_foreign_keys for dst_task: %s for src_tasks: %s', dst_task.id, str(src_tasks.ids))

        # find the many2one relation to a task

        Task = self.env['project.task']
        relations = self._get_fk_on('project_task')

        for table, column in relations:
            if 'base_task_merge_' in table:  # ignore two tables
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
                for task in src_tasks:
                    self._cr.execute(query, (dst_task.id, task.id, dst_task.id))
            else:
                try:
                    with mute_logger('odoo.sql_db'), self._cr.savepoint():
                        query = 'UPDATE "%(table)s" SET "%(column)s" = %%s WHERE "%(column)s" IN %%s' % query_dic
                        self._cr.execute(query, (dst_task.id, tuple(src_tasks.ids),))


                except psycopg2.Error:
                    # updating fails, most likely due to a violated unique constraint
                    # keeping record with nonexistent task_id is useless, better delete it
                    query = 'DELETE FROM "%(table)s" WHERE "%(column)s" IN %%s' % query_dic
                    self._cr.execute(query, (tuple(src_tasks.ids),))

    @api.model
    def _update_reference_fields(self, src_tasks, dst_task):
        """ Update all reference fields from the src_tasks to dst_task.
            :param src_tasks : merge source task.task recordset (does not include destination one)
            :param dst_task : record of destination task.task
        """
        _logger.debug('_update_reference_fields for dst_task: %s for src_tasks: %r', dst_task.id, src_tasks.ids)

        def update_records(model, src, field_model='model', field_id='res_id'):
            Model = self.env[model] if model in self.env else None
            if Model is None:
                return
            records = Model.sudo().search([(field_model, '=', 'project.task'), (field_id, '=', src.id)])
            try:
                with mute_logger('odoo.sql_db'), self._cr.savepoint():
                    return records.sudo().write({field_id: dst_task.id})
            except psycopg2.Error:
                # updating fails, most likely due to a violated unique constraint
                # keeping record with nonexistent task_id is useless, better delete it
                return records.sudo().unlink()

        update_records = functools.partial(update_records)

        for task in src_tasks:
            update_records('ir.attachment', src=task, field_model='res_model')
            update_records('mail.followers', src=task, field_model='res_model')
            update_records('mail.message', src=task)
            update_records('ir.model.data', src=task)

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

            for task in src_tasks:
                records_ref = Model.sudo().search([(record.name, '=', 'project.task,%d' % task.id)])
                values = {
                    record.name: 'project.task,%d' % dst_task.id,
                }
                records_ref.sudo().write(values)

    @api.model
    def _update_values(self, src_tasks, dst_task):
        """ Update values of dst_task with the ones from the src_tasks.
            :param src_tasks : recordset of source task.task
            :param dst_task : record of destination task.task
        """
        _logger.debug('_update_values for dst_task: %s for src_tasks: %r', dst_task.id, src_tasks.ids)

        model_fields = dst_task.fields_get().keys()

        def write_serializer(item):
            if isinstance(item, models.BaseModel):
                return item.id
            else:
                return item

        # get all fields that are not computed or x2many
        values = dict()
        for column in model_fields:
            field = dst_task._fields[column]
            if field.type not in ('many2many', 'one2many') and field.compute is None:
                for item in itertools.chain(src_tasks, [dst_task]):
                    if item[column]:
                        values[column] = write_serializer(item[column])
        # remove fields that can not be updated (id and parent_id)
        values.pop('id', None)
        parent_id = values.pop('parent_id', None)
        dst_task.write(values)
        # try to update the parent_id
        if parent_id and parent_id != dst_task.id:
            try:
                dst_task.write({'parent_id': parent_id})
            except ValidationError:
                _logger.info('Skip recursive task hierarchies for parent_id %s of task: %s', parent_id, dst_task.id)

    def _merge(self, task_ids, dst_task=None):
        """ private implementation of merge task
            :param task_ids : ids of task to merge
            :param dst_task : record of destination task.task
        """
        Task = self.env['project.task']
        task_ids = Task.browse(task_ids).exists()
        if len(task_ids) < 2:
            return

        if len(task_ids) > 10:
            raise UserError(_("For safety reasons, you cannot merge more than 10 task together.\n"
                              " You can re-open the wizard several times if needed."))

        # remove dst_task from tasks to merge
        if dst_task and dst_task in task_ids:
            src_tasks = task_ids - dst_task
        else:
            ordered_tasks = self._get_ordered_task(task_ids.ids)
            dst_task = ordered_tasks[-1]
            src_tasks = ordered_tasks[:-1]
        _logger.info("dst_task: %s", dst_task.id)

        # call sub methods to do the merge
        self._update_foreign_keys(src_tasks, dst_task)
        self._update_reference_fields(src_tasks, dst_task)
        self._update_values(src_tasks, dst_task)

        _logger.info('(uid = %s) merged the tasks %r with %s', self._uid, src_tasks.ids, dst_task.id)
        dst_task.message_post(body='%s %s' % (_("Merged with the following tasks:"), ", ".join(
            '%s  (ID %s)' % (p.name, p.id) for p in src_tasks)))

        # delete source task, since they are merged
        src_tasks.unlink()

        # ----------------------------------------
        # Helpers
        # ----------------------------------------

    @api.model
    def _generate_query(self, fields, maximum_group=100):
        """ Build the SQL query on task.task table to group them according to given criteria
            :param fields : list of column names to group by the tasks
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
            "FROM project_task",
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
        """ Returns the list of field names the task can be grouped (as merge
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
        """ Build the SQL query on task.tasktable to group them according to given criteria
            :param fields : list of column names to group by the tasks
            :param maximum_group : limit of the query
        """
        # make the list of column to group by in sql query
        sql_fields = []
        for field in fields:
            if field in ['name']:
                sql_fields.append('lower(%s)' % field)
            else:
                sql_fields.append(field)
        group_fields = ', '.join(sql_fields)

        # where clause : for given group by columns, only keep the 'not null' record
        filters = []
        for field in fields:
            if field in ['name']:
                filters.append((field, 'IS NOT', 'NULL'))
        criteria = ' AND '.join('%s %s %s' % (field, operator, value) for field, operator, value in filters)

        # build the query
        text = [
            "SELECT min(id), array_agg(id)",
            "FROM project_task",
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
        """ Returns the list of field names the task can be grouped (as merge
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
    def _task_use_in(self, aggr_ids, models):
        """ Check if there is no occurence of this group of task in the selected model
            :param aggr_ids : stringified list of task ids separated with a comma (sql array_agg)
            :param models : dict mapping a model name with its foreign key with task_task table
        """
        return any(
            self.env[model].search_count([(field, 'in', aggr_ids)])
            for model, field in models.items()
        )

    @api.model
    def _get_ordered_task(self, task_ids):
        """ Helper : returns a `task.task` recordset ordered by create_date/active fields
            :param task_ids : list of task ids to sort
        """
        tasks = self.env['project.task'].browse(task_ids)
        tasks = tasks.sorted(key=lambda p: (p.active, (p.create_date or '')), reverse=True)
        return tasks

    @api.multi
    def _compute_models(self):
        """ Compute the different models needed by the system if you want to exclude some tasks. """
        model_mapping = {}

        if 'account.move.line' in self.env and self.exclude_journal_item:
            model_mapping['account.move.line'] = 'task_id'
        return model_mapping

    # ----------------------------------------
    # Actions
    # ----------------------------------------

    @api.multi
    def action_skip(self):
        """ Skip this wizard line. Don't compute any thing, and simply redirect to the new step."""
        if self.current_line_id:
            self.current_line_id.unlink()
        return self._action_next_screen()

    @api.multi
    def _action_next_screen(self):
        """ return the action of the next screen ; this means the wizard is set to treat the
            next wizard line. Each line is a subset of task that can be merged together.
            If no line left, the end screen will be displayed (but an action is still returned).
        """
        self.invalidate_cache()  # FIXME: is this still necessary?
        values = {}
        if self.line_ids:
            # in this case, we try to find the next record.
            current_line = self.line_ids[0]
            current_task_ids = literal_eval(current_line.aggr_ids)
            values.update({
                'current_line_id': current_line.id,
                'task_ids': [(6, 0, current_task_ids)],
                'dst_task_id': self._get_ordered_task(current_task_ids)[-1].id,
                'state': 'selection',
            })
        else:
            values.update({
                'current_line_id': False,
                'task_ids': [],
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

    @api.multi
    def _process_query(self, query):
        """ Execute the select request and write the result in this wizard
            :param query : the SQL query used to fill the wizard line
        """
        self.ensure_one()
        model_mapping = self._compute_models()

        # group task query
        self._cr.execute(query)

        counter = 0
        for min_id, aggr_ids in self._cr.fetchall():
            # To ensure that the used tasks are accessible by the user
            tasks = self.env['project.task'].search([('id', 'in', aggr_ids)])
            if len(tasks) < 2:
                continue

            # exclude task according to options
            if model_mapping and self._task_use_in(tasks.ids, model_mapping):
                continue

            self.env['base.task.merge.line'].create({
                'wizard_id': self.id,
                'min_id': min_id,
                'aggr_ids': tasks.ids,
            })
            counter += 1

        self.write({
            'state': 'selection',
            'number_group': counter,
        })

        _logger.info("counter: %s", counter)

    @api.multi
    def action_start_manual_process(self):
        """ Start the process 'Merge with Manual Check'. Fill the wizard according to the group_by and exclude
            options, and redirect to the first step (treatment of first wizard line). After, for each subset of
            task to merge, the wizard will be actualized.
                - Compute the selected groups (with duplication)
                - If the user has selected the 'exclude_xxx' fields, avoid the tasks
        """
        self.ensure_one()
        groups = self._compute_selected_groupby()
        query = self._generate_query(groups, self.maximum_group)
        self._process_query(query)
        return self._action_next_screen()

    @api.multi
    def action_start_automatic_process(self):
        """ Start the process 'Merge Automatically'. This will fill the wizard with the same mechanism as 'Merge
            with Manual Check', but instead of refreshing wizard with the current line, it will automatically process
            all lines by merging task grouped according to the checked options.
        """
        self.ensure_one()
        self.action_start_manual_process()  # here we don't redirect to the next screen, since it is automatic process
        self.invalidate_cache()  # FIXME: is this still necessary?

        for line in self.line_ids:
            task_ids = literal_eval(line.aggr_ids)
            self._merge(task_ids)
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

    @api.multi
    def action_merge(self):
        """ Merge Task button. Merge the selected tasks, and redirect to
            the end screen (since there is no other wizard line to process.
        """
        if not self.task_ids:
            self.write({'state': 'finished'})
            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }

        self._merge(self.task_ids.ids, self.dst_task_id)

        if self.current_line_id:
            self.current_line_id.unlink()

        return self._action_next_screen()
