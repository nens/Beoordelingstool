# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BeoordelingstoolOverwriteShapefilesDialog
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

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'beoordelingstool_overwrite_shapefiles_dialog.ui'))



class BeoordelingstoolOverwriteShapefilesDialog(QtGui.QDialog, FORM_CLASS):

    # closingPlugin = pyqtSignal()

    output = pyqtSignal(object)


    def __init__(self, parent=None):
        """Constructor."""
        super(BeoordelingstoolOverwriteShapefilesDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.overwrite_shapefiles_true)
        self.buttonBox.rejected.connect(self.overwrite_shapefiles_false)

    def closeEvent(self, event):
        # self.closingPlugin.emit()
        # event.accept()
        pass


    def overwrite_shapefiles_true(self):
        """
        Returns true if the user wants to overwrite his shapefiles.

        Returns:
            (boolean) overwrite_shapefiles: True
        """
        overwrite_shapefiles = True
        self.output.emit(overwrite_shapefiles)
        self.close()


    def overwrite_shapefiles_false(self):
        """
        Returns false if the user does not want to overwrite his shapefiles.

        Returns:
            (boolean) overwrite_shapefiles: False
        """
        overwrite_shapefiles = False
        self.output.emit(overwrite_shapefiles)
        self.close()
