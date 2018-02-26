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
from qgis.core import QgsMapLayerRegistry
from qgis.utils import iface

# import constants
from .utils.constants import HERSTELMAATREGELEN
from .utils.constants import SHP_NAME_MANHOLES
from .utils.constants import SHP_NAME_PIPES
from .utils.constants import SHP_NAME_MEASURING_POINTS

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
        self.tabWidget.currentChanged.connect(self.tab_changed)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def tab_changed(self):
        """Change the active layer upon selecting another tab."""
        if self.tabWidget.currentIndex() == 1:
            # Set manholes as active layer
            manholes_layer = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_MANHOLES)[0]
            iface.setActiveLayer(manholes_layer)
        elif self.tabWidget.currentIndex() == 2:
            # Set pipes as active layer
            pipes_layer = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_PIPES)[0]
            iface.setActiveLayer(pipes_layer)
        elif self.tabWidget.currentIndex() == 3:
            # Set measuring_points as active layer
            measuring_points_layer = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_MEASURING_POINTS)[0]
            iface.setActiveLayer(measuring_points_layer)

    def add_herstelmaatregelen(self):
        """Add the herstelmaatregelen to the comboboxes"""
        self.field_combobox_manholes.addItems(HERSTELMAATREGELEN)
        self.field_combobox_pipes.addItems(HERSTELMAATREGELEN)
        self.field_combobox_measuring_points.addItems(HERSTELMAATREGELEN)

