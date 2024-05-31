import logging
import os

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    store_fname = fields.Char("Stored Filename", index=True)
    store_file_size = fields.Integer("Store File Size", compute="_compute_store_file_size", store=True)

    @api.depends("store_fname")
    def _compute_store_file_size(self):
        for attachment in self:
            if attachment.store_fname:
                file_name = self._full_path(attachment.store_fname)
                if os.path.exists(file_name):
                    attachment.store_file_size = os.path.getsize(file_name)
                else:
                    attachment.store_file_size = 0
            else:
                attachment.store_file_size = 0

    def getListOfFiles(self, dirName):
        # create a list of file and sub directories
        # names in the given directory
        if "checklist" in dirName:
            return []
        listOfFile = os.listdir(dirName)

        allFiles = list()
        # Iterate over all the entries
        for entry in listOfFile:
            # Create full path
            fullPath = os.path.join(dirName, entry)
            # If entry is a directory then get the list of files in this directory
            if os.path.isdir(fullPath):
                allFiles = allFiles + self.getListOfFiles(fullPath)
            else:
                allFiles.append(fullPath)

        return allFiles

    def _get_file_store_size(self, file_list):
        filestore = self._filestore()
        _logger.info("filestore: %s", filestore)

        # calcul dimensiune folder
        totalSize = 0
        for file in file_list:
            totalSize = totalSize + os.path.getsize(file)
        _logger.info("totalSize: %s", totalSize / 1024 / 1024)

    def check_filestore(self, delete=False):
        _logger.info("Beginning check_file")
        filestore = self._filestore()
        file_list = self.getListOfFiles(filestore)
        self._get_file_store_size(file_list)

        store_fnames = list()
        for file in file_list:
            store_fnames.append(file.split(filestore + "/")[1])

        params = {"store_fname": tuple(store_fnames)}
        self.env.cr.execute("SELECT store_fname FROM ir_attachment WHERE store_fname IN %(store_fname)s", params=params)
        attachments_file_list = {row[0] for row in self.env.cr.fetchall()}

        file_list_to_remove = list(set(store_fnames) - set(attachments_file_list))
        _logger.info("count file_list_to_remove: %s", len(file_list_to_remove))
        _logger.info("file_list_to_remove: %s", file_list_to_remove)
        if delete:
            for file in file_list_to_remove:
                os.unlink(self._full_path(file))

        file_list = self.getListOfFiles(filestore)
        self._get_file_store_size(file_list)
