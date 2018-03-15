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

import base64
import itertools
import mimetypes
import mimetools
import datetime
import json
import os
import shutil
import tempfile
import urllib2
import zipfile

from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import QPyNullVariant
from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QDesktopServices
from PyQt4.QtGui import QTableWidgetItem
from qgis.core import QgsExpression
from qgis.core import QgsFeatureRequest
from qgis.core import QgsMapLayerRegistry
from qgis.gui import QgsMessageBar
from qgis.utils import iface

from .beoordelingstool_login_dialog import BeoordelingstoolLoginDialog

# Import functions
from .utils.layer import get_layer_dir

# import constants
from .utils.constants import HERSTELMAATREGELEN
# json properties
from .utils.constants import JSON_NAME
from .utils.constants import JSON_KEY_PROJ
from .utils.constants import JSON_KEY_NAME
from .utils.constants import JSON_KEY_URL
from .utils.constants import JSON_KEY_SLUG
# Shapefile names
from .utils.constants import SHAPEFILE_LIST
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

        # General tab
        self.set_project_properties()
        self.pushbutton_upload_voortgang_json.clicked.connect(
            self.show_login_dialog_voortgang)
        self.pushbutton_upload_final_json.clicked.connect(
            self.show_login_dialog_final)

        # Manholes tab
        self.selected_manhole_id = 0
        self.pushbutton_get_selected_manhole.clicked.connect(
            self.get_selected_manhole)
        self.pushbutton_save_attribute_manholes.clicked.connect(
            self.save_beoordeling_putten)

        # Pipes tab
        self.selected_pipe_id = 0
        self.pushbutton_get_selected_pipe.clicked.connect(
            self.get_selected_pipe)
        self.pushbutton_save_attribute_pipes.clicked.connect(
            self.save_beoordeling_leidingen)
        self.pushbutton_pipe_to_measuring_point.clicked.connect(
            self.show_measuring_point)

        # Measuring points tab
        self.selected_measuring_point_id = 0
        self.pushbutton_get_selected_measuring_point.clicked.connect(
            self.get_selected_measuring_point)
        self.pushbutton_save_attribute_measuring_points.clicked.connect(
            self.save_beoordeling_measuring_points)
        self.pushbutton_measuring_points_previous.clicked.connect(
            self.show_previous_measuring_point)
        self.pushbutton_measuring_point_to_pipe.clicked.connect(
            self.show_pipe)
        self.pushbutton_measuring_points_next.clicked.connect(
            self.show_next_measuring_point)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def add_herstelmaatregelen(self):
        """Add the herstelmaatregelen to the comboboxes"""
        self.field_combobox_manholes.addItems(HERSTELMAATREGELEN)
        self.field_combobox_pipes.addItems(HERSTELMAATREGELEN)
        self.field_combobox_measuring_points.addItems(HERSTELMAATREGELEN)

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

    def set_project_properties(self):
        """
        Set the project name on the General tab of the dockwidget.
        The name of the project name property of the review.json in the same
        folder as the layer is used as the project name.
        """
        # Check if the manholes, pipes and measuring_points layers exist
        manholes_layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_MANHOLES)
        pipes_layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_PIPES)
        measuring_points_layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_MEASURING_POINTS)
        if manholes_layerList and pipes_layerList and measuring_points_layerList:
            # Get project name from the json saved in the same folder as the "manholes" layer
            layer_dir = get_layer_dir(manholes_layerList[0])
            json_path = os.path.join(layer_dir, JSON_NAME)
            try:
                data = json.load(open(json_path))
                if data[JSON_KEY_PROJ][JSON_KEY_NAME]:
                    self.label_project_name.setText(data[JSON_KEY_PROJ][JSON_KEY_NAME])
                else:
                    iface.messageBar().pushMessage("Warning", "No project name defined.", level=QgsMessageBar.WARNING, duration=0)
                if data[JSON_KEY_PROJ][JSON_KEY_URL]:
                    self.textedit_project_url.setText("<a href=google.com>{}</a>".format(data[JSON_KEY_PROJ][JSON_KEY_URL]))
                    # .clicked(QDesktopServices.openUrl(QUrl(data[JSON_KEY_PROJ][JSON_KEY_URL], QUrl.TolerantMode)))
                    # self.label_project_url.setText("<a href={}>{}</a>".format(data[JSON_KEY_PROJ][JSON_KEY_URL]))
                else:
                    iface.messageBar().pushMessage("Warning", "No project url defined.", level=QgsMessageBar.WARNING, duration=0)
            except:
                # TODO: bare except. Also fails when there's a json if it is without project url.
                iface.messageBar().pushMessage("Error", "No {} found.".format(JSON_NAME), level=QgsMessageBar.CRITICAL, duration=0)

    def show_login_dialog_voortgang(self):
        """
        Show the login dialog.

        If the user data typed in the login dialog is correct, a json
        is created from the shapefiles and uploaded to the server.
        """
        # Check if the manholes, pipes and measuring_points layers exist
        self.login_dialog = BeoordelingstoolLoginDialog()
        self.login_dialog.show()
        self.login_dialog.output.connect(self.upload_voortgang)

    def show_login_dialog_final(self):
        """
        Show the login dialog.

        If the user data typed in the login dialog is correct, a json
        is created from the shapefiles and uploaded to the server.
        """
        self.login_dialog = BeoordelingstoolLoginDialog()
        self.login_dialog.show()
        self.login_dialog.output.connect(self.upload_final)

    def upload_voortgang(self, user_data):
        """Upload the voortgang (json)."""
        print "voortgang"
        review_json = self.convert_shps_to_json()
        # upload json to server (get url from json)
        save_json_to_server(review_json, user_data)

    def upload_final(self, user_data):
        """Upload the final version (json + zip with shapefiles and qmls)."""
        print "final"
        review_json = self.convert_shps_to_json()
        # Upload JSON
        save_json_to_server(review_json, user_data)
        # Upload zip
        # Check if the manholes, pipes and measuring_points layers exist
        manholes_layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_MANHOLES)
        pipes_layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_PIPES)
        measuring_points_layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_MEASURING_POINTS)
        if manholes_layerList and pipes_layerList and measuring_points_layerList:
            # Get project name from the json saved in the same folder as the "manholes" layer
            layer_dir = get_layer_dir(manholes_layerList[0])
            temp_dir = tempfile.mkdtemp(prefix="beoordelingstool")
            project_name = review_json[JSON_KEY_PROJ][JSON_KEY_NAME]
            zip_url = review_json[JSON_KEY_PROJ][JSON_KEY_URL]
            create_zip(project_name, layer_dir, temp_dir)
            save_zip_to_server(project_name, temp_dir, zip_url, user_data)
            iface.messageBar().pushMessage("Info", "JSON and ZIP uploaded.", level=QgsMessageBar.INFO, duration=0)

    def convert_shps_to_json(self):
        """
        Convert the manholes, pipes and measuring points shapefiles to a json.

        Args:
            (dict) user_data: A dict containing the username and password.

        Returns:
            (dict) json_: A dict containing the information about the project and the shapefiles.
        """
        # Check if the manholes, pipes and measuring_points layers exist
        manholes_layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_MANHOLES)
        pipes_layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_PIPES)
        measuring_points_layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_MEASURING_POINTS)
        if manholes_layerList and pipes_layerList and measuring_points_layerList:
            # Get directory to save json in
            layer_dir = get_layer_dir(manholes_layerList[0])
            json_path = os.path.join(layer_dir, JSON_NAME)
            # Pipes
            pipes = create_pipes_json(pipes_layerList[0], measuring_points_layerList[0])
            # Manholes
            manholes = create_manholes_json(manholes_layerList[0])
            json_ = {}
            json_project = {}
            if json_path:
                data = json.load(open(json_path))
                if data[JSON_KEY_PROJ][JSON_KEY_NAME]:
                    json_project[JSON_KEY_NAME] = data[JSON_KEY_PROJ][JSON_KEY_NAME]
                else:
                    iface.messageBar().pushMessage("Error", "No project name found.", level=QgsMessageBar.CRITICAL, duration=0)
                    return json_
                if data[JSON_KEY_PROJ][JSON_KEY_URL]:
                    json_project[JSON_KEY_URL] = data[JSON_KEY_PROJ][JSON_KEY_URL]
                else:
                    iface.messageBar().pushMessage("Error", "No project url found.", level=QgsMessageBar.CRITICAL, duration=0)
                    return json_
                if data[JSON_KEY_PROJ][JSON_KEY_SLUG]:
                    json_project[JSON_KEY_SLUG] = data[JSON_KEY_PROJ][JSON_KEY_SLUG]
                else:
                    iface.messageBar().pushMessage("Error", "No project slug found.", level=QgsMessageBar.CRITICAL, duration=0)
                    return json_
            else:
                iface.messageBar().pushMessage("Error", "No json found.", level=QgsMessageBar.CRITICAL, duration=0)
                return
            json_[JSON_KEY_PROJ] = json_project
            json_["pipes"] = pipes
            json_["manholes"] = manholes
            with open("{}".format(json_path), 'w') as outfile:
                json.dump(json_, outfile, indent=2)
            return json_
        else:
            iface.messageBar().pushMessage("Warning", "You don't have a manholes, pipes and measuring_points layer.", level=QgsMessageBar.WARNING, duration=0)
            json_ = {}
            return json_


    def get_selected_manhole(self):
        layer = iface.activeLayer()
        fields = layer.dataProvider().fields()
        for f in layer.selectedFeatures():
            self.field_combobox_manholes.setCurrentIndex(self.field_combobox_manholes.findText(str(f["Herstelmaa"]))) \
                if self.field_combobox_manholes.findText(str(f["Herstelmaa"])) else self.field_combobox_manholes.setCurrentIndex(0)
            self.value_plaintextedit_manholes.setPlainText(f["Opmerking"] if type(f["Opmerking"]) is not QPyNullVariant else "")

            for index, field in enumerate(["CAA",
                                           "CAJ",
                                           "CAL",
                                           "CAM",
                                           "CAN",
                                           "CAO",
                                           "CAQ",
                                           "CAR",
                                           "CBA",
                                           "CBB",
                                           "CBC",
                                           "CBD",
                                           "CBE",
                                           "CBF",
                                           "CBH",
                                           "CBI",
                                           "CBJ",
                                           "CBK",
                                           "CBL",
                                           "CBM",
                                           "CBO",
                                           "CBP",
                                           "CCA",
                                           "CCB",
                                           "CCC",
                                           "CCD",
                                           "CCK",
                                           "CCM",
                                           "CCN",
                                           "CCO",
                                           "CCP",
                                           "CCQ",
                                           "CCR",
                                           "CCS",
                                           "CDA",
                                           "CDB",
                                           "CDC",
                                           "CDD"]):
                value = f[field] if type(f[field]) is not QPyNullVariant else ""
                self.tablewidget_manholes.setItem(0, index, QTableWidgetItem(value))

            self.selected_manhole_id = f.id()

    def save_beoordeling_putten(self):
        """Save herstelmaatregel and opmerking in the shapefile."""
        layer = iface.activeLayer()
        fid = self.selected_manhole_id
        herstelmaatregel = str(self.field_combobox_manholes.currentText())
        opmerking = str(self.value_plaintextedit_manholes.toPlainText())
        layer.startEditing()
        layer.changeAttributeValue(fid, 38, herstelmaatregel)  # Herstelmaatregel
        layer.changeAttributeValue(fid, 39, opmerking)  # Opmerking
        layer.commitChanges()
        layer.triggerRepaint()

    def get_selected_pipe(self):
        layer = iface.activeLayer()
        fields = layer.dataProvider().fields()
        for f in layer.selectedFeatures():
            self.field_combobox_pipes.setCurrentIndex(self.field_combobox_pipes.findText(str(f["Herstelmaa"]))) \
                if self.field_combobox_pipes.findText(str(f["Herstelmaa"])) else self.field_combobox_pipes.setCurrentIndex(0)
            self.value_plaintextedit_pipes.setPlainText(str(f["Opmerking"]) if type(f["Opmerking"]) is not QPyNullVariant else "")

            for index, field in enumerate(["AAA",
                                           "AAB",
                                           "AAD",
                                           "AAE",
                                           "AAF",
                                           "AAG",
                                           "AAJ",
                                           "AAK",
                                           "AAL",
                                           "AAM",
                                           "AAN",
                                           "AAO",
                                           "AAP",
                                           "AAQ",
                                           "ABA",
                                           "ABB",
                                           "ABC",
                                           "ABE",
                                           "ABF",
                                           "ABH",
                                           "ABI",
                                           "ABJ",
                                           "ABK",
                                           "ABL",
                                           "ABM",
                                           "ABP",
                                           "ABQ",
                                           "ABS",
                                           "ACA",
                                           "ACB",
                                           "ACC",
                                           "ACD",
                                           "ACG",
                                           "ACJ",
                                           "ACK",
                                           "ACM",
                                           "ACN",
                                           "ADA",
                                           "ADB",
                                           "ADC",
                                           "AXA",
                                           "AXB",
                                           "AXF",
                                           "AXG",
                                           "AXH"]):
                value = f[field] if type(f[field]) is not QPyNullVariant else ""
                self.tablewidget_pipes.setItem(0, index, QTableWidgetItem(value))
            self.selected_pipe_id = f.id()

    def save_beoordeling_leidingen(self):
        """Save herstelmaatregel and opmerking in the shapefile."""
        layer = iface.activeLayer()
        fid = self.selected_pipe_id
        herstelmaatregel = str(self.field_combobox_pipes.currentText())
        opmerking = str(self.value_plaintextedit_pipes.toPlainText())
        layer.startEditing()
        layer.changeAttributeValue(fid, 46, herstelmaatregel)  # Herstelmaatregel
        layer.changeAttributeValue(fid, 47, opmerking)  # Opmerking
        layer.commitChanges()
        layer.triggerRepaint()

    def show_measuring_point(self):
        """Show the measuring point that belongs to a certain pipe."""
        try:
            current_measuring_point_pipe_id = self.tablewidget_measuring_points.itemAt(0,0).text()
        except:  # No measuring point selected
            current_measuring_point_pipe_id = -1
        # if current_measuring_point_pipe_id != self.selected_pipe_id:
        layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_MEASURING_POINTS)
        if layerList:
            layer = layerList[0]
            expr = QgsExpression("\"PIPE_ID\" IS '{}'".format(self.selected_pipe_id))
            measuring_points = layer.getFeatures(QgsFeatureRequest(expr))  #.next()
            ids = [measuring_point.id() for measuring_point in measuring_points]  # select only the features for which the expression is true
            if ids:
                first_id = ids[0]
                last_id = ids[-1]
                # Show selected measuring point if it belongs to the selected pipe
                if self.selected_measuring_point_id >= first_id and self.selected_measuring_point_id <= last_id:
                    pass
                # Show first measuring point that belongs to the selected pipe:
                else:
                    self.selected_measuring_point_id = first_id
                layer.setSelectedFeatures([int(self.selected_measuring_point_id)])
                new_feature = layer.selectedFeatures()[0]

                # Set values
                self.field_combobox_measuring_points.setCurrentIndex(self.field_combobox_measuring_points.findText(str(new_feature["Herstelmaa"]))) \
                    if self.field_combobox_measuring_points.findText(str(new_feature["Herstelmaa"])) else self.field_combobox_measuring_points.setCurrentIndex(0)
                opmerking = new_feature["Opmerking"] if new_feature["Opmerking"] and type(new_feature["Opmerking"]) is not QPyNullVariant else ''
                self.value_plaintextedit_measuring_points.setPlainText(opmerking)
                self.tablewidget_measuring_points.setItem(0, 0, QTableWidgetItem(new_feature["PIPE_ID"]))
                self.tablewidget_measuring_points.setItem(0, 1, QTableWidgetItem(new_feature["A"]))
                self.tablewidget_measuring_points.setItem(0, 2, QTableWidgetItem(new_feature["B"]))
                self.tablewidget_measuring_points.setItem(0, 3, QTableWidgetItem(new_feature["C"]))
                self.tablewidget_measuring_points.setItem(0, 4, QTableWidgetItem(new_feature["D"]))
                self.tablewidget_measuring_points.setItem(0, 5, QTableWidgetItem(new_feature["E"]))
                self.tablewidget_measuring_points.setItem(0, 6, QTableWidgetItem(new_feature["F"]))
                self.tablewidget_measuring_points.setItem(0, 7, QTableWidgetItem(new_feature["G"]))
                self.tablewidget_measuring_points.setItem(0, 8, QTableWidgetItem(new_feature["I"]))
                self.tablewidget_measuring_points.setItem(0, 9, QTableWidgetItem(new_feature["J"]))
                self.tablewidget_measuring_points.setItem(0, 10, QTableWidgetItem(new_feature["K"] if new_feature["K"] else None))
                self.tablewidget_measuring_points.setItem(0, 11, QTableWidgetItem(new_feature["M"]))
                self.tablewidget_measuring_points.setItem(0, 12, QTableWidgetItem(new_feature["N"]))
                self.tablewidget_measuring_points.setItem(0, 13, QTableWidgetItem(new_feature["O"]))
                iface.setActiveLayer(layer)
                layer.triggerRepaint()
                # Go to measuring points tab
                self.tabWidget.setCurrentIndex(3)
            else:
                iface.messageBar().pushMessage("Warning", "There are no measuring points connected to this pipe.", level=QgsMessageBar.WARNING, duration=0)
        else:
            iface.messageBar().pushMessage("Error", "There is no measuring points layer.", level=QgsMessageBar.CRITICAL, duration=0)

    def get_selected_measuring_point(self):
        layer = iface.activeLayer()
        fields = layer.dataProvider().fields()
        for f in layer.selectedFeatures():
            self.field_combobox_measuring_points.setCurrentIndex(self.field_combobox_measuring_points.findText(str(f["Herstelmaa"]))) \
                if self.field_combobox_measuring_points.findText(str(f["Herstelmaa"])) else self.field_combobox_measuring_points.setCurrentIndex(0)
            self.value_plaintextedit_measuring_points.setPlainText(str(f["Opmerking"]) if type(f["Opmerking"]) is not QPyNullVariant else "")
            self.tablewidget_measuring_points.setItem(0, 0, QTableWidgetItem(f["PIPE_ID"]))
            self.tablewidget_measuring_points.setItem(0, 1, QTableWidgetItem(f["A"]))
            self.tablewidget_measuring_points.setItem(0, 2, QTableWidgetItem(f["B"]))
            self.tablewidget_measuring_points.setItem(0, 3, QTableWidgetItem(f["C"]))
            self.tablewidget_measuring_points.setItem(0, 4, QTableWidgetItem(f["D"]))
            self.tablewidget_measuring_points.setItem(0, 5, QTableWidgetItem(f["E"]))
            self.tablewidget_measuring_points.setItem(0, 6, QTableWidgetItem(f["F"]))
            self.tablewidget_measuring_points.setItem(0, 7, QTableWidgetItem(f["G"]))
            self.tablewidget_measuring_points.setItem(0, 8, QTableWidgetItem(f["I"]))
            self.tablewidget_measuring_points.setItem(0, 9, QTableWidgetItem(f["J"]))
            self.tablewidget_measuring_points.setItem(0, 10, QTableWidgetItem(f["K"]))
            self.tablewidget_measuring_points.setItem(0, 11, QTableWidgetItem(f["M"]))
            self.tablewidget_measuring_points.setItem(0, 12, QTableWidgetItem(f["N"]))
            self.tablewidget_measuring_points.setItem(0, 13, QTableWidgetItem(f["O"]))
            self.selected_measuring_point_id = f.id()

    def show_previous_measuring_point(self):
        """Show the next measuring point."""
        if self.selected_measuring_point_id <= 0:
            iface.messageBar().pushMessage("Info", "This pipe has no previous measuring point.", level=QgsMessageBar.INFO, duration=0)
            return
        current_measuring_point_id = self.selected_measuring_point_id
        current_pipe_id = self.selected_pipe_id

        layer = iface.activeLayer()
        features_amount = layer.featureCount()
        measuring_point_id_new = self.selected_measuring_point_id - 1
        if measuring_point_id_new > -1:
            layer.setSelectedFeatures([int(measuring_point_id_new)])
            new_feature = layer.selectedFeatures()[0]
            pipe_id_new = int(new_feature["PIPE_ID"])
            # Only show the new measuring point if it belongs to the same
            # pipe
            if current_pipe_id == pipe_id_new:
                # Set values
                self.selected_measuring_point_id = measuring_point_id_new
                # Update Measuring points tab and tablewidget
                self.field_combobox_measuring_points.setCurrentIndex(self.field_combobox_measuring_points.findText(str(new_feature["Herstelmaa"]))) \
                    if self.field_combobox_measuring_points.findText(str(new_feature["Herstelmaa"])) else self.field_combobox_measuring_points.setCurrentIndex(0)
                opmerking = new_feature["Opmerking"] if new_feature["Opmerking"] and type(new_feature["Opmerking"]) is not QPyNullVariant else ''
                self.value_plaintextedit_measuring_points.setPlainText(opmerking)
                self.tablewidget_measuring_points.setItem(0, 0, QTableWidgetItem(new_feature["PIPE_ID"]))
                self.tablewidget_measuring_points.setItem(0, 1, QTableWidgetItem(new_feature["A"]))
                self.tablewidget_measuring_points.setItem(0, 2, QTableWidgetItem(new_feature["B"]))
                self.tablewidget_measuring_points.setItem(0, 3, QTableWidgetItem(new_feature["C"]))
                self.tablewidget_measuring_points.setItem(0, 4, QTableWidgetItem(new_feature["D"]))
                self.tablewidget_measuring_points.setItem(0, 5, QTableWidgetItem(new_feature["E"]))
                self.tablewidget_measuring_points.setItem(0, 6, QTableWidgetItem(new_feature["F"]))
                self.tablewidget_measuring_points.setItem(0, 7, QTableWidgetItem(new_feature["G"]))
                self.tablewidget_measuring_points.setItem(0, 8, QTableWidgetItem(new_feature["I"]))
                self.tablewidget_measuring_points.setItem(0, 9, QTableWidgetItem(new_feature["J"]))
                self.tablewidget_measuring_points.setItem(0, 10, QTableWidgetItem(new_feature["K"] if new_feature["K"] else None))
                self.tablewidget_measuring_points.setItem(0, 11, QTableWidgetItem(new_feature["M"]))
                self.tablewidget_measuring_points.setItem(0, 12, QTableWidgetItem(new_feature["N"]))
                self.tablewidget_measuring_points.setItem(0, 13, QTableWidgetItem(new_feature["O"]))
                layer.triggerRepaint()
            else:
                layer.setSelectedFeatures([int(self.selected_measuring_point_id)])
                iface.messageBar().pushMessage("Info", "This pipe has no previous measuring point.", level=QgsMessageBar.INFO, duration=0)


    def show_pipe(self):
        """Show the pipe to which a measuring point belongs."""
        pipe_id = int(self.tablewidget_measuring_points.itemAt(0,0).text()) if self.tablewidget_measuring_points.itemAt(0,0) else 1
        self.selected_pipe_id = pipe_id
        layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_PIPES)
        if layerList:
            layer = layerList[0]
            layer.setSelectedFeatures([self.selected_pipe_id])
            new_feature = layer.selectedFeatures()[0]
            self.field_combobox_pipes.setCurrentIndex(self.field_combobox_pipes.findText(str(new_feature["Herstelmaa"]))) \
                if self.field_combobox_pipes.findText(str(new_feature["Herstelmaa"])) else self.field_combobox_pipes.setCurrentIndex(0)
            self.value_plaintextedit_pipes.setPlainText(str(new_feature["Opmerking"]) if type(new_feature["Opmerking"]) is not QPyNullVariant else "")
            self.tablewidget_pipes.setItem(0, 0, QTableWidgetItem(new_feature["AAA"]))
            self.tablewidget_pipes.setItem(0, 1, QTableWidgetItem(new_feature["AAB"]))
            self.tablewidget_pipes.setItem(0, 2, QTableWidgetItem(new_feature["AAD"]))
            self.tablewidget_pipes.setItem(0, 3, QTableWidgetItem(new_feature["AAE"]))
            self.tablewidget_pipes.setItem(0, 4, QTableWidgetItem(new_feature["AAF"]))
            self.tablewidget_pipes.setItem(0, 5, QTableWidgetItem(new_feature["AAG"]))
            self.tablewidget_pipes.setItem(0, 6, QTableWidgetItem(new_feature["AAJ"]))
            self.tablewidget_pipes.setItem(0, 7, QTableWidgetItem(new_feature["AAK"]))
            self.tablewidget_pipes.setItem(0, 8, QTableWidgetItem(new_feature["AAL"]))
            self.tablewidget_pipes.setItem(0, 9, QTableWidgetItem(new_feature["AAM"]))
            self.tablewidget_pipes.setItem(0, 10, QTableWidgetItem(new_feature["AAN"]))
            self.tablewidget_pipes.setItem(0, 11, QTableWidgetItem(new_feature["AAO"]))
            self.tablewidget_pipes.setItem(0, 12, QTableWidgetItem(new_feature["AAP"]))
            self.tablewidget_pipes.setItem(0, 13, QTableWidgetItem(new_feature["AAQ"]))
            self.tablewidget_pipes.setItem(0, 14, QTableWidgetItem(new_feature["ABA"]))
            self.tablewidget_pipes.setItem(0, 15, QTableWidgetItem(new_feature["ABB"]))
            self.tablewidget_pipes.setItem(0, 16, QTableWidgetItem(new_feature["ABC"]))
            self.tablewidget_pipes.setItem(0, 17, QTableWidgetItem(new_feature["ABE"]))
            self.tablewidget_pipes.setItem(0, 18, QTableWidgetItem(new_feature["ABF"]))
            self.tablewidget_pipes.setItem(0, 19, QTableWidgetItem(new_feature["ABH"]))
            self.tablewidget_pipes.setItem(0, 20, QTableWidgetItem(new_feature["ABI"]))
            self.tablewidget_pipes.setItem(0, 21, QTableWidgetItem(new_feature["ABJ"]))
            self.tablewidget_pipes.setItem(0, 22, QTableWidgetItem(new_feature["ABK"]))
            self.tablewidget_pipes.setItem(0, 23, QTableWidgetItem(new_feature["ABL"]))
            self.tablewidget_pipes.setItem(0, 24, QTableWidgetItem(new_feature["ABM"]))
            self.tablewidget_pipes.setItem(0, 25, QTableWidgetItem(new_feature["ABP"]))
            self.tablewidget_pipes.setItem(0, 26, QTableWidgetItem(new_feature["ABQ"]))
            self.tablewidget_pipes.setItem(0, 27, QTableWidgetItem(new_feature["ABS"]))
            self.tablewidget_pipes.setItem(0, 28, QTableWidgetItem(new_feature["ACA"]))
            self.tablewidget_pipes.setItem(0, 29, QTableWidgetItem(new_feature["ACB"]))
            self.tablewidget_pipes.setItem(0, 30, QTableWidgetItem(new_feature["ACC"]))
            self.tablewidget_pipes.setItem(0, 31, QTableWidgetItem(new_feature["ACD"]))
            self.tablewidget_pipes.setItem(0, 32, QTableWidgetItem(new_feature["ACG"]))
            self.tablewidget_pipes.setItem(0, 33, QTableWidgetItem(new_feature["ACJ"]))
            self.tablewidget_pipes.setItem(0, 34, QTableWidgetItem(new_feature["ACK"]))
            self.tablewidget_pipes.setItem(0, 35, QTableWidgetItem(new_feature["ACM"]))
            self.tablewidget_pipes.setItem(0, 36, QTableWidgetItem(new_feature["ACN"]))
            self.tablewidget_pipes.setItem(0, 37, QTableWidgetItem(new_feature["ADA"]))
            self.tablewidget_pipes.setItem(0, 38, QTableWidgetItem(new_feature["ADB"]))
            self.tablewidget_pipes.setItem(0, 39, QTableWidgetItem(new_feature["ADC"]))
            self.tablewidget_pipes.setItem(0, 40, QTableWidgetItem(new_feature["AXA"]))
            self.tablewidget_pipes.setItem(0, 41, QTableWidgetItem(new_feature["AXB"]))
            self.tablewidget_pipes.setItem(0, 42, QTableWidgetItem(new_feature["AXF"]))
            self.tablewidget_pipes.setItem(0, 43, QTableWidgetItem(new_feature["AXG"]))
            self.tablewidget_pipes.setItem(0, 44, QTableWidgetItem(new_feature["AXH"]))
            iface.setActiveLayer(layer)
            layer.triggerRepaint()
            # Go to the pipe tab
            self.tabWidget.setCurrentIndex(2)

    def show_next_measuring_point(self):
        """Show the next measuring point."""
        # Only show if still same pipe
        # Show message if first id and clicked on again (can't go further)
        current_measuring_point_id = self.selected_measuring_point_id
        current_pipe_id = self.selected_pipe_id

        layer = iface.activeLayer()
        features_amount = layer.featureCount()
        measuring_point_id_new = self.selected_measuring_point_id + 1
        if measuring_point_id_new < features_amount:
            layer.setSelectedFeatures([int(self.selected_measuring_point_id) + 1])
            new_feature = layer.selectedFeatures()[0]
            pipe_id_new = int(new_feature["PIPE_ID"])
            # Only show the new measuring point if it belongs to the same
            # pipe
            if current_pipe_id == pipe_id_new:
                # Set values
                self.selected_measuring_point_id = measuring_point_id_new
                # Update Measuring points tab and tablewidget

                self.field_combobox_measuring_points.setCurrentIndex(self.field_combobox_measuring_points.findText(str(new_feature["Herstelmaa"]))) \
                    if self.field_combobox_measuring_points.findText(str(new_feature["Herstelmaa"])) else self.field_combobox_measuring_points.setCurrentIndex(0)
                opmerking = new_feature["Opmerking"] if new_feature["Opmerking"] and type(new_feature["Opmerking"]) is not QPyNullVariant else ''
                self.value_plaintextedit_measuring_points.setPlainText(opmerking)
                self.tablewidget_measuring_points.setItem(0, 0, QTableWidgetItem(new_feature["PIPE_ID"]))
                self.tablewidget_measuring_points.setItem(0, 1, QTableWidgetItem(new_feature["A"]))
                self.tablewidget_measuring_points.setItem(0, 2, QTableWidgetItem(new_feature["B"]))
                self.tablewidget_measuring_points.setItem(0, 3, QTableWidgetItem(new_feature["C"]))
                self.tablewidget_measuring_points.setItem(0, 4, QTableWidgetItem(new_feature["D"]))
                self.tablewidget_measuring_points.setItem(0, 5, QTableWidgetItem(new_feature["E"]))
                self.tablewidget_measuring_points.setItem(0, 6, QTableWidgetItem(new_feature["F"]))
                self.tablewidget_measuring_points.setItem(0, 7, QTableWidgetItem(new_feature["G"]))
                self.tablewidget_measuring_points.setItem(0, 8, QTableWidgetItem(new_feature["I"]))
                self.tablewidget_measuring_points.setItem(0, 9, QTableWidgetItem(new_feature["J"]))
                self.tablewidget_measuring_points.setItem(0, 10, QTableWidgetItem(new_feature["K"] if new_feature["K"] else None))
                self.tablewidget_measuring_points.setItem(0, 11, QTableWidgetItem(new_feature["M"]))
                self.tablewidget_measuring_points.setItem(0, 12, QTableWidgetItem(new_feature["N"]))
                self.tablewidget_measuring_points.setItem(0, 13, QTableWidgetItem(new_feature["O"]))
                layer.triggerRepaint()
            else:
                layer.setSelectedFeatures([int(self.selected_measuring_point_id)])
                iface.messageBar().pushMessage("Info", "This pipe has no next measuring point.", level=QgsMessageBar.INFO, duration=0)

    def save_beoordeling_measuring_points(self):
        """Save herstelmaatregel and opmerking in the shapefile."""
        layer = iface.activeLayer()
        fid = self.selected_measuring_point_id
        herstelmaatregel = str(self.field_combobox_measuring_points.currentText())
        opmerking = str(self.value_plaintextedit_measuring_points.toPlainText())
        layer.startEditing()
        layer.changeAttributeValue(fid, 16, herstelmaatregel)  # Herstelmaatregel
        layer.changeAttributeValue(fid, 17, opmerking)  # Opmerking
        layer.commitChanges()
        layer.triggerRepaint()


def create_manholes_json(manholes_layer):
    """
    Create a manholes dict from the manholes shapefile.

    Args:
        (shapefile) manholes_shapefile: The manholes shapefile.

    Returns:
        (dict) manholes: A dict containing the information from the
            manholes shapefile.
    """
    manholes_list = []
    for feature in manholes_layer.getFeatures():
        herstelmaatregel = str(feature["Herstelmaa"]) if str(feature["Herstelmaa"]) is not "NULL" else ""
        opmerking = str(feature["Opmerking"]) if str(feature["Opmerking"]) is not "NULL" else ""
        manhole = {
            "CRS": "Netherlands-RD",
            "CDC": str(feature["CDC"]),
            "CCK": str(feature["CCK"]),
            "CAR": str(feature["CAR"]),
            "CAQ": str(feature["CAQ"]),
            "CCQ": str(feature["CCQ"]),
            "CCP": str(feature["CCP"]),
            "CCS": str(feature["CCS"]),
            "CCR": str(feature["CCR"]),
            "CCM": str(feature["CCM"]),
            "CAJ": str(feature["CAJ"]),
            "CCO": str(feature["CCO"]),
            "CCN": str(feature["CCN"]),
            "CAO": str(feature["CAO"]),
            "CAN": str(feature["CAN"]),
            "CAM": str(feature["CAM"]),
            "CAL": str(feature["CAL"]),
            "CCD": str(feature["CCD"]),
            "CAA": str(feature["CAA"]),
            "CCA": str(feature["CCA"]),
            "CCC": str(feature["CCC"]),
            "CCB": str(feature["CCB"]),
            "CDD": str(feature["CDD"]),
            "Herstelmaatregel": herstelmaatregel,
            "CDB": str(feature["CDB"]),
            "CBB": str(feature["CBB"]),
            "CBC": str(feature["CBC"]),
            "CBA": str(feature["CBA"]),
            "CBF": str(feature["CBF"]),
            "CDA": str(feature["CDA"]),
            "CBD": str(feature["CBD"]),
            "CBE": str(feature["CBE"]),
            "CBJ": str(feature["CBJ"]),
            "CBK": str(feature["CBK"]),
            "CBH": str(feature["CBH"]),
            "CBI": str(feature["CBI"]),
            "CBO": str(feature["CBO"]),
            "CBL": str(feature["CBL"]),
            "CBM": str(feature["CBM"]),
            "CBP": str(feature["CBP"]),
            "Opmerking": opmerking,
            "y": str(feature.geometry().asPoint().y()),
            "x": str(feature.geometry().asPoint().x()),
        }
        manholes_list.append(manhole)

    return manholes_list

def create_pipes_json(pipes_layer, measuring_points_layer):
    """
    Create a pipes dict from the pipes and measuring points shapefile.
    One pipe can have 0/> measuring points.

    Args:
        (shapefile) pipes_shapefile: The pipes shapefile.
        (shapefile) measuring_points_shapefile: The measuring points shapefile.

    Returns:
        (dict) pipes: A dict containing the information from the
            pipes and measuring points shapefile.
    """
    idx = measuring_points_layer.fieldNameIndex("PIPE_ID")
    values = measuring_points_layer.uniqueValues(idx)
    pipes_list = []
    # Loop through pipes shapefile and add features of shapefile to the json
    for feature in pipes_layer.getFeatures():
        herstelmaatregel = str(feature["Herstelmaa"]) if str(feature["Herstelmaa"]) is not "NULL" else ""
        opmerking = str(feature["Opmerking"]) if str(feature["Opmerking"]) is not "NULL" else ""
        pipe = {
            "AAE": feature["AAE"].split(', '),
            "AAD": str(feature["AAD"]),
            "AAG": feature["AAG"].split(', '),
            "AAF": str(feature["AAF"]),
            "AAA": str(feature["AAA"]),
            "Beginpunt y": str(feature.geometry().asPolyline()[0].y()),
            "Beginpunt x": str(feature.geometry().asPolyline()[0].x()),
            "AAM": str(feature["AAM"]),
            "AAL": str(feature["AAL"]),
            "AAO": str(feature["AAO"]),
            "AAN": str(feature["AAN"]),
            "Eindpunt CRS": "Netherlands-RD",
            "AAK": str(feature["AAK"]),
            "AAJ": str(feature["AAJ"]),
            "ACD": str(feature["ACD"]),
            "AXA": str(feature["AXA"]),
            "AAQ": str(feature["AAQ"]),
            "AAP": str(feature["AAP"]),
            "ACG": str(feature["ACG"]),
            "AXH": str(feature["AXH"]),
            "AXG": str(feature["AXG"]),
            "AAB": str(feature["AAB"]),
            "ACK": str(feature["ACK"]),
            "ACJ": str(feature["ACJ"]),
            "Beginpunt CRS": "Netherlands-RD",
            "ACC": str(feature["ACC"]),
            "ABA": str(feature["ABA"]),
            "ABB": str(feature["ABB"]),
            "ABC": str(feature["ABC"]),
            "ACN": str(feature["ACN"]),
            "ABE": str(feature["ABE"]),
            "ABF": str(feature["ABF"]),
            "ABH": str(feature["ABH"]),
            "ABI": str(feature["ABI"]),
            "ABJ": str(feature["ABJ"]),
            "ABK": str(feature["ABK"]),
            "ABL": str(feature["ABL"]),
            "ABM": str(feature["ABM"]),
            "ABP": str(feature["ABP"]),
            "ABQ": str(feature["ABQ"]),
            "ABS": str(feature["ABS"]),
            "ADB": str(feature["ADB"]),
            "ACM": str(feature["ACM"]),
            "ADA": str(feature["ADA"]),
            "ACB": str(feature["ACB"]),
            "AXB": str(feature["AXB"]),
            "Herstelmaatregel": herstelmaatregel,
            "Eindpunt y": str(feature.geometry().asPolyline()[-1].y()),
            "Eindpunt x": str(feature.geometry().asPolyline()[-1].x()),
            "Opmerking": opmerking,
            "AXF": str(feature["AXF"]),
            "ACA": str(feature["ACA"]),
            "ADC": str(feature["ADC"]),
        }
        # Add measuring points to the pipe, if the pipe has measuring
        # points
        if feature["ID"] in values:
            expr = QgsExpression("\"PIPE_ID\" = '{}'".format(feature["ID"]))
            request = QgsFeatureRequest(expr)
            measuring_points_layer_specific_pipe = measuring_points_layer.getFeatures(request)
            pipe["ZC"] = create_measuring_points_list(measuring_points_layer_specific_pipe)
        pipes_list.append(pipe)

    return pipes_list

def create_measuring_points_list(measuring_points_layer):
    """
    Create a list from the measuring points shapefile.
    A list item is a json, representing a measuring points.

    Args:
        (shapefile) measuring_points_layer: The measuring points
            shapefile.

    Returns:
        (list) measuring_points_list: A list containing the information from
            the measuring points shapefile. A list item is a measuring
            point, represented by a json.
    """
    measuring_points_list = []
    for feature in measuring_points_layer:
        measuring_point = {}
        if feature["A"] and feature["A"] != "None": measuring_point["A"] = str(feature["A"])
        if feature["B"] and feature["B"] != "None": measuring_point["B"] = str(feature["B"])
        if feature["C"] and feature["C"] != "None": measuring_point["C"] = str(feature["C"])
        if feature["D"] and feature["D"] != "None": measuring_point["D"] = str(feature["D"])
        if feature["E"] and feature["E"] != "None": measuring_point["E"] = str(feature["E"])
        if feature["F"] and feature["F"] != "None": measuring_point["F"] = str(feature["F"])
        if feature["G"] and feature["G"] != "None": measuring_point["G"] = str(feature["G"])
        if feature["I"] and feature["I"] != "None": measuring_point["I"] = str(feature["I"])
        if feature["J"] and feature["J"] != "None": measuring_point["J"] = str(feature["J"])
        if feature["K"] and feature["K"] != "None": measuring_point["K"] = str(feature["K"])
        if feature["M"] and feature["M"] != "None": measuring_point["M"] = str(feature["M"])
        if feature["N"] and feature["N"] != "None": measuring_point["N"] = str(feature["N"])
        if feature["O"] and feature["O"] != "None": measuring_point["O"] = str(feature["O"])
        herstelmaatregel = str(feature["Herstelmaa"]) if str(feature["Herstelmaa"]) is not "NULL" else ""
        measuring_point["Herstelmaatregel"] = herstelmaatregel
        opmerking = str(feature["Opmerking"]) if str(feature["Opmerking"]) is not "NULL" else ""
        measuring_point["Opmerking"] = opmerking
        # x & y of measuring points json are saved in the json as tuples  #  x': (146777.899562,)
        measuring_point["y"] = float(feature.geometry().asPoint().y())
        measuring_point["x"] = float(feature.geometry().asPoint().x())
        measuring_points_list.append(measuring_point)
    return measuring_points_list

def save_json_to_server(review_json, user_data):
    """
    Upload a json to the review_json[JSON_KEY_PROJ][JSON_KEY_URL].

    Args:
        (dict) review_json: A dict containing the json url and the json to save to the server
        (dict) user_data: A dict containing the username and password.
    """
    # Check user login credentials ()  # not needed, checked when json is uploaded
    username = user_data["username"]
    password = user_data["password"]
    if review_json[JSON_KEY_PROJ][JSON_KEY_URL] is None:
        iface.messageBar().pushMessage("Error", "The json has no url.", level=QgsMessageBar.CRITICAL, duration=0)
        return
    else:
        manholes_layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_MANHOLES)
        pipes_layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_PIPES)
        measuring_points_layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_MEASURING_POINTS)
        if manholes_layerList and pipes_layerList and measuring_points_layerList:
            # Get project name from the json saved in the same folder as the "manholes" layer
            layer_dir = get_layer_dir(manholes_layerList[0])
            json_path = os.path.join(layer_dir, JSON_NAME)

            form = MultiPartForm()
            filename = os.path.basename(json_path)
            form.add_field('Upload reviews', 'Upload reviews')
            form.add_file('reviews', filename, fileHandle=open(json_path, 'rb'))

            url = review_json[JSON_KEY_PROJ][JSON_KEY_URL]
            request = urllib2.Request(url)
            request.add_header('User-agent', 'beoordelingstool')
            request.add_header('username', username)
            request.add_header('password', password)
            body = str(form)
            request.add_header('Content-type', form.get_content_type())
            request.add_header('Content-length', len(body))
            request.add_data(body)

            fd2, logfile = tempfile.mkstemp(prefix="uploadlog", suffix=".txt")
            open(logfile, 'w').write(request.get_data())

            answer = urllib2.urlopen(request).read()
            iface.messageBar().pushMessage("Info", "JSON uploaded.",
                level=QgsMessageBar.INFO, duration=20)

def create_zip(project_name, layer_dir, temp_dir):  # for zip_file_name in querysets
    """
    Create zipfile.
    The zipfile is downloaded in the temp folder and contains the shapefiles and
    an json-file.

    Args:
        (str) project)name: The name of the project, this will also become the
            name of the zipfile.
        (str) layer_dir: The name of the directory where the manholes layer is saved.
        (str) temp_dir: The name of the temp directory.
    """
    dest_filename = os.path.join(temp_dir, project_name)
    shutil.make_archive(dest_filename, 'zip', layer_dir)  # 'zip' is added as '.zip' as extension


def save_zip_to_server(project_name, temp_dir, zip_url, user_data):
    """
    Save a zip-file (containing three ESRI shapefiles and a review.json) to
    the server (zip_url).

    Args:
        (str) project_name: The name of the zip-file to save to the server.
        (str) temp_dir: The path to the temp directory.
        (str) zip_url: The url to save the zip to.
        (dict) user_data: A dict containing the username and password
    """
    # Check user login credentials ()  # not needed, checked when json is uploaded
    username = user_data["username"]
    password = user_data["password"]
    if zip_url is None:
        iface.messageBar().pushMessage("Error", "The json has no url.", level=QgsMessageBar.CRITICAL, duration=0)
        return
    else:
        manholes_layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_MANHOLES)
        pipes_layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_PIPES)
        measuring_points_layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_MEASURING_POINTS)
        if manholes_layerList and pipes_layerList and measuring_points_layerList:
            # Get project name from the json saved in the same folder as the "manholes" layer
            layer_dir = get_layer_dir(manholes_layerList[0])
            zip_path = os.path.join(layer_dir, "{}.zip".format(project_name))

            form = MultiPartForm()
            filename = os.path.basename(zip_path)
            form.add_field('Upload reviews', 'Upload reviews')
            form.add_file('shape_files', filename, fileHandle=open(zip_path, 'rb'))

            url = review_json[JSON_KEY_PROJ][JSON_KEY_URL]
            request = urllib2.Request(url)
            request.add_header('User-agent', 'beoordelingstool')
            request.add_header('username', username)
            request.add_header('password', password)
            body = str(form)
            request.add_header('Content-type', form.get_content_type())
            request.add_header('Content-length', len(body))
            request.add_data(body)

            fd2, logfile = tempfile.mkstemp(prefix="uploadlog", suffix=".txt")
            open(logfile, 'w').write(request.get_data())

            answer = urllib2.urlopen(request).read()
            iface.messageBar().pushMessage("Info", "JSON uploaded.",
                level=QgsMessageBar.INFO, duration=20)


class MultiPartForm(object):
    """Accumulate the data to be used when posting a form."""

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()
        return

    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
        return

    def add_file(self, fieldname, filename, fileHandle, mimetype=None):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        if mimetype is None:
            mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        self.files.append((fieldname, filename, mimetype, body))
        return

    def __str__(self):
        """Return a string representing the form data, including attached files."""
        # Build a list of lists, each containing "lines" of the
        # request.  Each part is separated by a boundary string.
        # Once the list is built, return a string where each
        # line is separated by '\r\n'.
        parts = []
        part_boundary = '--' + self.boundary

        # Add the form fields
        parts.extend(
            [ part_boundary,
              'Content-Disposition: form-data; name="%s"' % name,
              '',
              value,
            ]
            for name, value in self.form_fields
            )

        # Add the files to upload
        parts.extend(
            [ part_boundary,
              'Content-Disposition: file; name="%s"; filename="%s"' % \
                 (field_name, filename),
              'Content-Type: %s' % content_type,
              '',
              body,
            ]
            for field_name, filename, content_type, body in self.files
            )

        # Flatten the list and add closing boundary marker,
        # then return CR+LF separated data
        flattened = list(itertools.chain(*parts))
        flattened.append('--' + self.boundary + '--')
        flattened.append('')
        return '\r\n'.join(flattened)
