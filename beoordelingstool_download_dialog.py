# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BeoordelingstoolDownloadDialog
                                 A QGIS plugin
 The Beoordelingstool is a QGIS plugin for judging the quality of the manholes and pipes of a sewer.
                             -------------------
        begin                : 2017-04-26
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Nelen & Schuurmans
        email                : madeleine.vanwinkel@nelen-schuurmans.nl
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt4 import QtGui, uic
from PyQt4.QtCore import QSettings
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QFileDialog
from qgis.gui import QgsMessageBar
from qgis.utils import iface

BUTTON_DOWNLOAD_RIOOL = "download_riool_search"
TEXTBOX_DOWNLOAD_RIOOL = "download_riool_text"
# from .utils.constants import BUTTON_DOWNLOAD_PUTTEN
# from .utils.constants import TEXTBOX_DOWNLOAD_PUTTEN
FILE_TYPE_JSON = "json"
# HERSTELMAATREGEL_DEFAULT = 1
# from .utils.constants import FILE_TYPE_JSON
# from .utils.get_data import get_file

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'beoordelingstool_download_dialog.ui'))


class BeoordelingstoolDownloadDialog(QtGui.QDialog, FORM_CLASS):

    # closingPlugin = pyqtSignal()


    def __init__(self, parent=None):
        """Constructor."""
        super(BeoordelingstoolDownloadDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.download_riool_search.clicked.connect(
                    self.search_json_riool)

    def closeEvent(self, event):
        # self.closingPlugin.emit()
        # event.accept()
        pass

    def set_filename(self, TEXTBOX, filename):
        """Set the filename in the proper textbox."""
        if TEXTBOX == TEXTBOX_DOWNLOAD_PUTTEN:
            self.download_rioolputten_text.setText(filename)

    def search_json_riool(self):
        """Get the json of 'Rioolputten'."""
        self.search_file(BUTTON_DOWNLOAD_RIOOL)

    def search_file(self, BUTTON):
        """Function to search a file."""
        if BUTTON == BUTTON_DOWNLOAD_RIOOL:
            textbox = TEXTBOX_DOWNLOAD_RIOOL
        file_type = FILE_TYPE_JSON
        filename = self.get_file(file_type)
        self.set_filename(textbox, filename)

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

    def set_filename(self, TEXTBOX, filename):
            """Set the filename in the proper textbox."""
            if TEXTBOX == TEXTBOX_DOWNLOAD_RIOOL:
                self.download_riool_text.setText(filename)
                # print filename  # riool.json

