# # -*- coding: utf-8 -*-
# """Module for getting data from files."""
import os.path

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QFileDialog

from .constants import FILE_TYPE_JSON


def get_file(self, file_type):
    """Function to get a file."""
    settings = QSettings('beoordelingstool', 'qgisplugin')

    try:
        init_path = settings.value('last_used_import_path', type=str)
    except TypeError:
        init_path = os.path.expanduser("~")
    if file_type == FILE_TYPE_JSON:
      filename = QFileDialog.getOpenFileName(None,
                                             'Select import file',
                                             init_path,
                                             'JSON (*.json)')

    if filename:
        settings.setValue('last_used_import_path',
                          os.path.dirname(filename))

    return filename
