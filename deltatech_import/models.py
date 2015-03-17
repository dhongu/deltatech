import csv
import itertools
import logging
import operator
import openerp
from openerp.api import Environment
from openerp.osv import orm, fields

_logger = logging.getLogger(__name__) 

class ir_import(orm.TransientModel):
    _inherit = 'base_import.import'


    def _convert_import_data(self, record, fields, options, context=None):
        """ Extracts the input browse_record and fields list (with
        ``False``-y placeholders for fields to *not* import) into a
        format Model.import_data can use: a fields list without holes
        and the precisely matching data matrix

        :param browse_record record:
        :param list(str|bool): fields
        :returns: (data, fields)
        :rtype: (list(list(str)), list(str))
        :raises ValueError: in case the import data could not be converted
        """
        # Get indices for non-empty fields
        indices = [index for index, field in enumerate(fields) if field]
        if not indices:
            raise ValueError(_("You must configure at least one field to import"))
        # If only one index, itemgetter will return an atom rather
        # than a 1-tuple
        if len(indices) == 1: mapper = lambda row: [row[indices[0]]]
        else: mapper = operator.itemgetter(*indices)
        # Get only list of actually imported fields
        import_fields = filter(None, fields)

        rows_to_import = self._read_csv(record, options)
        fromline = int(options.get('fromline','0'))
        
        toline = options.get('toline','max')
        if toline == 'max':
            toline = None
        else:
            toline = int(toline)
            
        if options.get('headers') and fromline == 0:
            fromline = 1
        rows_to_import = itertools.islice(
            rows_to_import,  fromline ,  toline )            
        data = [
            row for row in itertools.imap(mapper, rows_to_import)
            # don't try inserting completely empty rows (e.g. from
            # filtering out o2m fields)
            if any(row)
        ]

        return data, import_fields

    def do(self, cr, uid, id, fields, options, dryrun=False, context=None):
        """ Actual execution of the import

        :param fields: import mapping: maps each column to a field,
                       ``False`` for the columns to ignore
        :type fields: list(str|bool)
        :param dict options:
        :param bool dryrun: performs all import operations (and
                            validations) but rollbacks writes, allows
                            getting as much errors as possible without
                            the risk of clobbering the database.
        :returns: A list of errors. If the list is empty the import
                  executed fully and correctly. If the list is
                  non-empty it contains dicts with 3 keys ``type`` the
                  type of error (``error|warning``); ``message`` the
                  error message associated with the error (a string)
                  and ``record`` the data which failed to import (or
                  ``false`` if that data isn't available or provided)
        :rtype: list({type, message, record})
        """
        

        (record,) = self.browse(cr, uid, [id], context=context)
        try:
            data, import_fields = self._convert_import_data(
                record, fields, options, context=context)
        except ValueError, e:
            return [{
                'type': 'error',
                'message': unicode(e),
                'record': False,
            }]
            
        _logger.info('importing %d rows...', len(data))            
        
         
        to_index = 0
        with Environment.manage():
            while to_index < len(data):
           
                new_cr = self.pool.cursor()

                new_cr.close()            
                if dryrun:   
                    local_cr = cr
                else:  
                    local_cr =  self.pool.cursor()           
                
                if dryrun:
                    local_cr.execute('SAVEPOINT import')
                from_index = to_index 
                to_index = from_index + 99
                if  to_index > len(data):
                    to_index = len(data)
    
                _logger.info('importing rows from %d to %d...',   from_index, to_index  )
                
                import_result = self.pool[record.res_model].load(
                    local_cr, uid, import_fields, data[from_index:to_index], context=context)  
                
                _logger.info('done')
                to_index = to_index + 1
                # If transaction aborted, RELEASE SAVEPOINT is going to raise
                # an InternalError (ROLLBACK should work, maybe). Ignore that.
                # TODO: to handle multiple errors, create savepoint around
                #       write and release it in case of write error (after
                #       adding error to errors array) => can keep on trying to
                #       import stuff, and rollback at the end if there is any
                #       error in the results.
                try:
                    if dryrun:
                        local_cr.execute('ROLLBACK TO SAVEPOINT import')
                    else:
                        ##cr.execute('RELEASE SAVEPOINT import')
                        _logger.info('commit')
                        local_cr.commit()
                        local_cr.close()
                        
                except psycopg2.InternalError:
                    break

        return import_result['messages']
