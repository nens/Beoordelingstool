# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BeoordelingstoolDockWidget
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
from PyQt4.QtCore import pyqtSignal

from .utils.constants import HERSTELMAATREGELEN

TEXTBOX_DOWNLOAD_PUTTEN = "download_rioolputten_text"

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'beoordelingstool_dockwidget_base.ui'))


class BeoordelingstoolDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(BeoordelingstoolDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.add_herstelmaatregelen()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def add_herstelmaatregelen(self):
        """Add the herstelmaatregelen to the comboboxes"""
        self.field_combobox_manholes.addItems(HERSTELMAATREGELEN)
        self.field_combobox_pipes.addItems(HERSTELMAATREGELEN)
        self.field_combobox_measuring_stations.addItems(HERSTELMAATREGELEN)

    def set_filename(self, TEXTBOX, filename):
        """Set the filename in the proper textbox."""
        if TEXTBOX == TEXTBOX_DOWNLOAD_PUTTEN:
            self.download_rioolputten_text.setText(filename)

