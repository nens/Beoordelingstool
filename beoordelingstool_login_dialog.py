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
from PyQt4.QtCore import pyqtSignal

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'beoordelingstool_login_dialog.ui'))


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
        # # Set focus to uername lineedit
        # self.lineedit_username.setFocus()  # dows noet set input focus
        # Get json
        # self.download_riool_search.clicked.connect(self.search_json_riool)
        # Save json in 3 shapefiles: manholes, pipes and measuring_points
        self.accepted.connect(self.get_user_data)
        # # Show dockwidget after pressing OK with all 3 layers
        # self.accepted.connect(self.show_dockwidget)
        # self.json_path = ''
        # user_data = self.get_user_data()

    def closeEvent(self, event):
        # self.closingPlugin.emit()
        # event.accept()
        pass

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
        # Clear lineEdits
        self.lineedit_username.clear()
        self.lineedit_password.clear()
        # Emit the user data
        self.output.emit(user_data)