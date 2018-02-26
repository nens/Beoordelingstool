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
import json

from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal
from qgis.core import QgsMapLayerRegistry

from .utils.layer import get_layer_dir

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'beoordelingstool_login_dialog.ui'))

# Import constants
from .utils.constants import JSON_NAME
from .utils.constants import JSON_KEY_PROJ
from .utils.constants import JSON_KEY_USERNAME


class BeoordelingstoolLoginDialog(QtGui.QDialog, FORM_CLASS):

    # closingPlugin = pyqtSignal()

    output = pyqtSignal(object)


    def __init__(self, parent=None):
        """Constructor."""
        super(BeoordelingstoolLoginDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.set_username()
        # # Set focus to uername lineedit
        # self.lineedit_username.setFocus()  # dows noet set input focus
        self.accepted.connect(self.get_user_data)

    def closeEvent(self, event):
        # self.closingPlugin.emit()
        # event.accept()
        pass

    def set_username(self):
    	"""Set the username in the login dialog."""
        manholes_layerList = QgsMapLayerRegistry.instance().mapLayersByName("manholes")
        pipes_layerList = QgsMapLayerRegistry.instance().mapLayersByName("pipes")
        measuring_stations_layerList = QgsMapLayerRegistry.instance().mapLayersByName("measuring_points")
        if manholes_layerList and pipes_layerList and measuring_stations_layerList:
            # Get directory to save json in
            layer_dir = get_layer_dir(manholes_layerList[0])
            json_path = os.path.join(layer_dir, JSON_NAME)
            review_json = json.load(open(json_path))
            if review_json[JSON_KEY_PROJ][JSON_KEY_USERNAME]:
	            username = review_json[JSON_KEY_PROJ][JSON_KEY_USERNAME]
	            self.lineedit_username.setText(username)

    def get_user_data(self):
        """
        Get the username and password.

        Returns:
            (dict) user_data: A dict containing the keys username and password
                with their data from the line edit.
        """

        username = self.lineedit_username.text()
        password = self.lineedit_password.text()
        user_data = {
            "username": username,
            "password": password
        }
        # Check user credentials
        # Emit the user data
        self.output.emit(user_data)
        # Clear lineEdits
        self.lineedit_username.clear()
        self.lineedit_password.clear()
