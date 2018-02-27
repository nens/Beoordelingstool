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
import json
import os
import tempfile
import urllib2
import zipfile

from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import QPyNullVariant
from PyQt4.QtGui import QDesktopServices
from PyQt4.QtGui import QTableWidgetItem
from qgis.core import QgsExpression
from qgis.core import QgsFeatureRequest
from qgis.core import QgsMapLayerRegistry
from qgis.gui import QgsMessageBar
from qgis.utils import iface

from beoordelingstool_login_dialog import BeoordelingstoolLoginDialog

# Import functions
from .utils.layer import get_layer_dir

# import constants
from .utils.constants import HERSTELMAATREGELEN
# json properties
from .utils.constants import JSON_NAME
from .utils.constants import JSON_KEY_PROJ
from .utils.constants import JSON_KEY_NAME
from .utils.constants import JSON_KEY_URL
from .utils.constants import JSON_KEY_URL_JSON
from .utils.constants import JSON_KEY_URL_ZIP
from .utils.constants import JSON_KEY_USERNAME
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
        # Create the login dialog for uploading the voortgang
        self.login_dialog_voortgang = BeoordelingstoolLoginDialog()
        self.login_dialog_voortgang.output.connect(self.upload_voortgang)
        # Create the login dialog for uploading the final version
        self.login_dialog_final = BeoordelingstoolLoginDialog()
        self.login_dialog_final.output.connect(self.upload_final)
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

        # Measuring stations tab
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
                    self.textedit_project_url.setText("<a href=google.com>{}</a>".format(data[JSON_KEY_PROJ][JSON_KEY_URL])).clicked(QDesktopServices.openUrl(QUrl(data[JSON_KEY_PROJ][JSON_KEY_URL], QUrl.TolerantMode)))
                    # self.label_project_url.setText("<a href={}>{}</a>".format(data[JSON_KEY_PROJ][JSON_KEY_URL]))
                else:
                    iface.messageBar().pushMessage("Warning", "No project url defined.", level=QgsMessageBar.WARNING, duration=0)
            except:
                iface.messageBar().pushMessage("Error", "No {} found.".format(JSON_NAME), level=QgsMessageBar.CRITICAL, duration=0)

    def show_login_dialog_voortgang(self):
        """
        Show the login dialog.

        If the user data typed in the login dialog is correct, a json
        is created from the shapefiles and uploaded to the server.
        """
        # Check if the manholes, pipes and measuring_points layers exist
        self.login_dialog_voortgang.show()
        # manholes_layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_MANHOLES)
        # pipes_layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_PIPES)
        # measuring_points_layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_MEASURING_POINTS)
        # if manholes_layerList and pipes_layerList and measuring_points_layerList:
        #     # Check user login credentials ()
        #     username = "Aagje_opdr_nemer"
        #     self.login_dialog_voortgang = BeoordelingstoolLoginDialog()
        #     self.login_dialog_voortgang.lineedit_username.setText(username)
        #     self.login_dialog_voortgang.show()

    def show_login_dialog_final(self):
        """
        Show the login dialog.

        If the user data typed in the login dialog is correct, a json
        is created from the shapefiles and uploaded to the server.
        """
        self.login_dialog_final.show()

    def upload_voortgang(self, user_data):
        """Upload the voortgang (json)."""
        print "voortgang"
        review_json = self.convert_shps_to_json()
        # save_json_to_server(review_json, user_data)
        # upload json to server (get url from json)
        iface.messageBar().pushMessage("Info", "JSON saved.", level=QgsMessageBar.INFO, duration=0)

    def upload_final(self, user_data):
        """Upload the final version (json + zip with shapefiles and qmls)."""
        print "final"
        review_json = self.convert_shps_to_json()
        # Upload JSON
        # save_json_to_server(review_json, user_data)
        # Upload zip
        temp_dir = tempfile.mkdtemp(prefix="beoordelingstool")
        project_name = review_json[JSON_KEY_PROJ][JSON_KEY_NAME]
        zip_url = review_json[JSON_KEY_PROJ][JSON_KEY_URL_ZIP]
        # create_zip(project_name, temp_dir)
        # save_zip_to_server(project_name, temp_dir, zip_url, user_data)
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
                if data[JSON_KEY_PROJ][JSON_KEY_USERNAME]:
                    json_project[JSON_KEY_USERNAME] = data[JSON_KEY_PROJ][JSON_KEY_USERNAME]
                else:
                    iface.messageBar().pushMessage("Error", "No username found.", level=QgsMessageBar.CRITICAL, duration=0)
                    return json_
                if data[JSON_KEY_PROJ][JSON_KEY_URL]:
                    json_project[JSON_KEY_URL] = data[JSON_KEY_PROJ][JSON_KEY_URL]
                else:
                    iface.messageBar().pushMessage("Error", "No project url found.", level=QgsMessageBar.CRITICAL, duration=0)
                    return json_
                if data[JSON_KEY_PROJ][JSON_KEY_URL_JSON]:
                    json_project[JSON_KEY_URL_JSON] = data[JSON_KEY_PROJ][JSON_KEY_URL_JSON]
                else:
                    iface.messageBar().pushMessage("Error", "No upload url found for the JSON.", level=QgsMessageBar.CRITICAL, duration=0)
                    return json_
                if data[JSON_KEY_PROJ][JSON_KEY_URL_ZIP]:
                    json_project[JSON_KEY_URL_ZIP] = data[JSON_KEY_PROJ][JSON_KEY_URL_ZIP]
                else:
                    iface.messageBar().pushMessage("Error", "No upload url found for the zip-file.", level=QgsMessageBar.CRITICAL, duration=0)
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
            self.field_combobox_manholes.setCurrentIndex(self.field_combobox_manholes.findText(str(f["Herstelmaa"]))) if self.field_combobox_manholes.findText(str(f["Herstelmaa"])) else self.field_combobox_manholes.setCurrentIndex(0)
            self.value_plaintextedit_manholes.setPlainText(f["Opmerking"] if type(f["Opmerking"]) is not QPyNullVariant else "")
            self.tablewidget_manholes.setItem(0, 0, QTableWidgetItem(f["CAA"]))
            self.tablewidget_manholes.setItem(0, 1, QTableWidgetItem(f["CAJ"]))
            self.tablewidget_manholes.setItem(0, 2, QTableWidgetItem(f["CAL"]))
            self.tablewidget_manholes.setItem(0, 3, QTableWidgetItem(f["CAM"]))
            self.tablewidget_manholes.setItem(0, 4, QTableWidgetItem(f["CAN"]))
            self.tablewidget_manholes.setItem(0, 5, QTableWidgetItem(f["CAO"]))
            self.tablewidget_manholes.setItem(0, 6, QTableWidgetItem(f["CAQ"]))
            self.tablewidget_manholes.setItem(0, 7, QTableWidgetItem(f["CAR"]))
            self.tablewidget_manholes.setItem(0, 8, QTableWidgetItem(f["CBA"]))
            self.tablewidget_manholes.setItem(0, 9, QTableWidgetItem(f["CBB"]))
            self.tablewidget_manholes.setItem(0, 10, QTableWidgetItem(f["CBC"]))
            self.tablewidget_manholes.setItem(0, 11, QTableWidgetItem(f["CBD"]))
            self.tablewidget_manholes.setItem(0, 12, QTableWidgetItem(f["CBE"]))
            self.tablewidget_manholes.setItem(0, 13, QTableWidgetItem(f["CBF"]))
            self.tablewidget_manholes.setItem(0, 14, QTableWidgetItem(f["CBH"]))
            self.tablewidget_manholes.setItem(0, 15, QTableWidgetItem(f["CBI"]))
            self.tablewidget_manholes.setItem(0, 16, QTableWidgetItem(f["CBJ"]))
            self.tablewidget_manholes.setItem(0, 17, QTableWidgetItem(f["CBK"]))
            self.tablewidget_manholes.setItem(0, 18, QTableWidgetItem(f["CBL"]))
            self.tablewidget_manholes.setItem(0, 19, QTableWidgetItem(f["CBM"]))
            self.tablewidget_manholes.setItem(0, 20, QTableWidgetItem(f["CBO"]))
            self.tablewidget_manholes.setItem(0, 21, QTableWidgetItem(f["CBP"]))
            self.tablewidget_manholes.setItem(0, 22, QTableWidgetItem(f["CCA"]))
            self.tablewidget_manholes.setItem(0, 23, QTableWidgetItem(f["CCB"]))
            self.tablewidget_manholes.setItem(0, 24, QTableWidgetItem(f["CCC"]))
            self.tablewidget_manholes.setItem(0, 25, QTableWidgetItem(f["CCD"]))
            self.tablewidget_manholes.setItem(0, 26, QTableWidgetItem(f["CCK"]))
            self.tablewidget_manholes.setItem(0, 27, QTableWidgetItem(f["CCM"]))
            self.tablewidget_manholes.setItem(0, 28, QTableWidgetItem(f["CCN"]))
            self.tablewidget_manholes.setItem(0, 29, QTableWidgetItem(f["CCO"]))
            self.tablewidget_manholes.setItem(0, 30, QTableWidgetItem(f["CCP"]))
            self.tablewidget_manholes.setItem(0, 31, QTableWidgetItem(f["CCQ"]))
            self.tablewidget_manholes.setItem(0, 32, QTableWidgetItem(f["CCR"]))
            self.tablewidget_manholes.setItem(0, 33, QTableWidgetItem(f["CCS"]))
            self.tablewidget_manholes.setItem(0, 34, QTableWidgetItem(f["CDA"]))
            self.tablewidget_manholes.setItem(0, 35, QTableWidgetItem(f["CDB"]))
            self.tablewidget_manholes.setItem(0, 36, QTableWidgetItem(f["CDC"]))
            self.tablewidget_manholes.setItem(0, 37, QTableWidgetItem(f["CDD"]))
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
            self.field_combobox_pipes.setCurrentIndex(self.field_combobox_pipes.findText(str(f["Herstelmaa"]))) if self.field_combobox_pipes.findText(str(f["Herstelmaa"])) else self.field_combobox_pipes.setCurrentIndex(0)
            self.value_plaintextedit_pipes.setPlainText(str(f["Opmerking"]) if type(f["Opmerking"]) is not QPyNullVariant else "")
            self.tablewidget_pipes.setItem(0, 0, QTableWidgetItem(f["AAA"]))
            self.tablewidget_pipes.setItem(0, 1, QTableWidgetItem(f["AAB"]))
            self.tablewidget_pipes.setItem(0, 2, QTableWidgetItem(f["AAD"]))
            self.tablewidget_pipes.setItem(0, 3, QTableWidgetItem(f["AAE"]))
            self.tablewidget_pipes.setItem(0, 4, QTableWidgetItem(f["AAF"]))
            self.tablewidget_pipes.setItem(0, 5, QTableWidgetItem(f["AAG"]))
            self.tablewidget_pipes.setItem(0, 6, QTableWidgetItem(f["AAJ"]))
            self.tablewidget_pipes.setItem(0, 7, QTableWidgetItem(f["AAK"]))
            self.tablewidget_pipes.setItem(0, 8, QTableWidgetItem(f["AAL"]))
            self.tablewidget_pipes.setItem(0, 9, QTableWidgetItem(f["AAM"]))
            self.tablewidget_pipes.setItem(0, 10, QTableWidgetItem(f["AAN"]))
            self.tablewidget_pipes.setItem(0, 11, QTableWidgetItem(f["AAO"]))
            self.tablewidget_pipes.setItem(0, 12, QTableWidgetItem(f["AAP"]))
            self.tablewidget_pipes.setItem(0, 13, QTableWidgetItem(f["AAQ"]))
            self.tablewidget_pipes.setItem(0, 14, QTableWidgetItem(f["ABA"]))
            self.tablewidget_pipes.setItem(0, 15, QTableWidgetItem(f["ABB"]))
            self.tablewidget_pipes.setItem(0, 16, QTableWidgetItem(f["ABC"]))
            self.tablewidget_pipes.setItem(0, 17, QTableWidgetItem(f["ABE"]))
            self.tablewidget_pipes.setItem(0, 18, QTableWidgetItem(f["ABF"]))
            self.tablewidget_pipes.setItem(0, 19, QTableWidgetItem(f["ABH"]))
            self.tablewidget_pipes.setItem(0, 20, QTableWidgetItem(f["ABI"]))
            self.tablewidget_pipes.setItem(0, 21, QTableWidgetItem(f["ABJ"]))
            self.tablewidget_pipes.setItem(0, 22, QTableWidgetItem(f["ABK"]))
            self.tablewidget_pipes.setItem(0, 23, QTableWidgetItem(f["ABL"]))
            self.tablewidget_pipes.setItem(0, 24, QTableWidgetItem(f["ABM"]))
            self.tablewidget_pipes.setItem(0, 25, QTableWidgetItem(f["ABP"]))
            self.tablewidget_pipes.setItem(0, 26, QTableWidgetItem(f["ABQ"]))
            self.tablewidget_pipes.setItem(0, 27, QTableWidgetItem(f["ABS"]))
            self.tablewidget_pipes.setItem(0, 28, QTableWidgetItem(f["ACA"]))
            self.tablewidget_pipes.setItem(0, 29, QTableWidgetItem(f["ACB"]))
            self.tablewidget_pipes.setItem(0, 30, QTableWidgetItem(f["ACC"]))
            self.tablewidget_pipes.setItem(0, 31, QTableWidgetItem(f["ACD"]))
            self.tablewidget_pipes.setItem(0, 32, QTableWidgetItem(f["ACG"]))
            self.tablewidget_pipes.setItem(0, 33, QTableWidgetItem(f["ACJ"]))
            self.tablewidget_pipes.setItem(0, 34, QTableWidgetItem(f["ACK"]))
            self.tablewidget_pipes.setItem(0, 35, QTableWidgetItem(f["ACM"]))
            self.tablewidget_pipes.setItem(0, 36, QTableWidgetItem(f["ACN"]))
            self.tablewidget_pipes.setItem(0, 37, QTableWidgetItem(f["ADA"]))
            self.tablewidget_pipes.setItem(0, 38, QTableWidgetItem(f["ADB"]))
            self.tablewidget_pipes.setItem(0, 39, QTableWidgetItem(f["ADC"]))
            self.tablewidget_pipes.setItem(0, 40, QTableWidgetItem(f["AXA"]))
            self.tablewidget_pipes.setItem(0, 41, QTableWidgetItem(f["AXB"]))
            self.tablewidget_pipes.setItem(0, 42, QTableWidgetItem(f["AXF"]))
            self.tablewidget_pipes.setItem(0, 43, QTableWidgetItem(f["AXG"]))
            self.tablewidget_pipes.setItem(0, 44, QTableWidgetItem(f["AXH"]))
            self.selected_pipe_id = f.id()

    def save_beoordeling_leidingen(self):
        """Save herstelmaatregel and opmerking in the shapefile."""
        layer = iface.activeLayer()
        fid = self.selected_pipe_id
        herstelmaatregel = str(self.field_combobox_pipes.currentText())
        opmerking = str(self.value_plaintextedit_pipes.toPlainText())
        layer.startEditing()
        layer.changeAttributeValue(fid, 47, herstelmaatregel)  # Herstelmaatregel
        layer.changeAttributeValue(fid, 48, opmerking)  # Opmerking
        layer.commitChanges()
        layer.triggerRepaint()

    def show_measuring_point(self):
        """Show the measuring station that belongs to a certain pipe."""
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
            first_id = ids[0]
            last_id = ids[-1] if ids[-1] else ids[0]
            # Show selected measuring station if it belongs to the selected pipe
            if self.selected_measuring_point_id >= first_id and self.selected_measuring_point_id <= last_id:
                pass
            # Show first measuring station that belongs to the selected pipe:
            else:
                self.selected_measuring_point_id = first_id
            layer.setSelectedFeatures([int(self.selected_measuring_point_id)])
            new_feature = layer.selectedFeatures()[0]

            # Set values
            self.field_combobox_measuring_points.setCurrentIndex(self.field_combobox_measuring_points.findText(str(new_feature["Herstelmaa"]))) if self.field_combobox_measuring_points.findText(str(new_feature["Herstelmaa"])) else self.field_combobox_measuring_points.setCurrentIndex(0)
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
            # Go to measuring stations tab
            self.tabWidget.setCurrentIndex(3)

    def get_selected_measuring_point(self):
        layer = iface.activeLayer()
        fields = layer.dataProvider().fields()
        for f in layer.selectedFeatures():
            self.field_combobox_measuring_points.setCurrentIndex(self.field_combobox_measuring_points.findText(str(f["Herstelmaa"]))) if self.field_combobox_measuring_points.findText(str(f["Herstelmaa"])) else self.field_combobox_measuring_points.setCurrentIndex(0)
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
        """Show the next measuring station."""
        if self.selected_measuring_point_id <= 0:
            iface.messageBar().pushMessage("Info", "This pipe has no previous measuring station.", level=QgsMessageBar.INFO, duration=0)
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
            # Only show the new measuring station if it belongs to the same
            # pipe
            if current_pipe_id == pipe_id_new:
                # Set values
                self.selected_measuring_point_id = measuring_point_id_new
                # Update Measuring stations tab and tablewidget
                self.field_combobox_measuring_points.setCurrentIndex(self.field_combobox_measuring_points.findText(str(new_feature["Herstelmaa"]))) if self.field_combobox_measuring_points.findText(str(new_feature["Herstelmaa"])) else self.field_combobox_measuring_points.setCurrentIndex(0)
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
                iface.messageBar().pushMessage("Info", "This pipe has no previous measuring station.", level=QgsMessageBar.INFO, duration=0)


    def show_pipe(self):
        """Show the pipe to which a measuring station belongs."""
        pipe_id = self.tablewidget_measuring_points.itemAt(0,0).text() if self.tablewidget_measuring_points.itemAt(0,0) else 1
        self.selected_pipe_id = pipe_id
        layerList = QgsMapLayerRegistry.instance().mapLayersByName(SHP_NAME_PIPES)
        if layerList:
            layer = layerList[0]
            layer.setSelectedFeatures([int(self.selected_pipe_id)])
            new_feature = layer.selectedFeatures()[0]
            self.field_combobox_pipes.setCurrentIndex(self.field_combobox_pipes.findText(str(new_feature["Herstelmaa"]))) if self.field_combobox_pipes.findText(str(new_feature["Herstelmaa"])) else self.field_combobox_pipes.setCurrentIndex(0)
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
        """Show the next measuring station."""
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
            # Only show the new measuring station if it belongs to the same
            # pipe
            if current_pipe_id == pipe_id_new:
                # Set values
                self.selected_measuring_point_id = measuring_point_id_new
                # Update Measuring stations tab and tablewidget

                self.field_combobox_measuring_points.setCurrentIndex(self.field_combobox_measuring_points.findText(str(new_feature["Herstelmaa"]))) if self.field_combobox_measuring_points.findText(str(new_feature["Herstelmaa"])) else self.field_combobox_measuring_points.setCurrentIndex(0)
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
                iface.messageBar().pushMessage("Info", "This pipe has no next measuring station.", level=QgsMessageBar.INFO, duration=0)

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
    Create a pipes dict from the pipes and measuring stations shapefile.
    One pipe can have 0/> measuring stations.

    Args:
        (shapefile) pipes_shapefile: The pipes shapefile.
        (shapefile) measuring_points_shapefile: The measuring stations shapefile.

    Returns:
        (dict) pipes: A dict containing the information from the
            pipes and measuring stations shapefile.
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
        # Add measuring stations to the pipe, if the pipe has measuring
        # stations
        if feature["ID"] in values:
            expr = QgsExpression("\"PIPE_ID\" = '{}'".format(feature["ID"]))
            request = QgsFeatureRequest(expr)
            measuring_points_layer_specific_pipe = measuring_points_layer.getFeatures(request)
        pipes_list.append(pipe)

    return pipes_list


def save_json_to_server(review_json, user_data):
    """
    Upload a json to the review_json[JSON_KEY_PROJ][JSON_KEY_URL_JSON].

    Args:
        (dict) review_json: A dict containing the json url and the json to save to the server
        (dict) user_data: A dict containing the username and password.
    """
    # Check user login credentials ()  # not needed, checked when json is uploaded
    # username = user_data["username"]
    # password = user_data["password"]
    if review_json[JSON_KEY_PROJ][JSON_KEY_URL_JSON] is None:
        iface.messageBar().pushMessage("Error", "The json has no json url.", level=QgsMessageBar.CRITICAL, duration=0)
        return
    else:
        url = review_json[JSON_KEY_PROJ][JSON_KEY_URL_JSON]
        encoded_user = base64.b64encode(user_data)
        req = urllib2.Request(url, review_json, encoded_user)
        response = urllib2.urlopen(req)
        the_page = reponse.read()  # nodig
    # # GGMN  https://github.com/nens/ggmn-qgis/blob/master/lizard_downloader.py#L534
    # form = urllib2_upload.MultiPartForm()
    # form.add_field('title', title)
    # form.add_field('organisation_id', str(self.selected_organisation))
    # filename = os.path.basename(tiff_filename)
    # form.add_file('raster_file', filename, fileHandle=open(tiff_filename, 'rb'))

    # request = urllib2.Request('https://ggmn.un-igrac.org/upload_raster/')
    # request.add_header('User-agent', 'qgis ggmn uploader')
    # request.add_header('username', self.username)
    # request.add_header('password', self.password)
    # body = str(form)
    # request.add_header('Content-type', form.get_content_type())
    # request.add_header('Content-length', len(body))
    # # print("content-length: %s" % len(body))
    # request.add_data(body)

    # fd2, logfile = tempfile.mkstemp(prefix="uploadlog", suffix=".txt")
    # open(logfile, 'w').write(request.get_data())
    # # print("Printed what we'll send to %s" % logfile)

    # answer = urllib2.urlopen(request).read()
    # # print(answer)
    # # print("Uploaded geotiff to the server")
    # pop_up_info("Uploaded geotiff to the server")

def create_zip(project_name, temp_dir):  # for zip_file_name in querysets
    """
    Create zipfile.
    The zipfile is downloaded in the temp folder and contains the shapefiles and
    an json-file.

    Args:
        (str) project)name: The name of the project, this will also become the
            name of the zipfile.
        (str) temp_dir: The name of the temp directory.
    """
    # Add shapefiles
    for name in SHAPEFILE_LIST:
        dbf_path = os.path.join(temp_dir, "{}.dbf".format(name))
        prj_path = os.path.join(temp_dir, "{}.prj".format(name))
        qml_path = os.path.join(temp_dir, "{}.qml".format(name))
        shp_path = os.path.join(temp_dir, "{}.shp".format(name))
        shx_path = os.path.join(temp_dir, "{}.shx".format(name))
        with zipfile.ZipFile(os.path.abspath(os.path.join(temp_dir, "{}.zip".format(project_name))), 'w') as myzip:
            myzip.write(shp_path)
            myzip.write(dbf_path)
            myzip.write(prj_path)
            myzip.write(shx_path)
            myzip.write(qml_path)
    # Add JSON
    json_path = os.path.join(temp_dir, "{}".format(JSON_NAME))
    with zipfile.ZipFile(os.path.abspath(os.path.join(temp_dir, "{}.zip".format(project_name))), 'w') as myzip:
        myzip.write(json_path)


def save_zip_to_server(project_name, temp_dir, zip_url, user_data):
    """
    Save a zip-file (containing an ESRI shapefile and accompanying ini-file) to the server (zip_url).

    Args:
        (str) project_name: The name of the zip-file to save to the server.
        (str) temp_dir: The path to the temp directory.
        (str) zip_url: The url to save the zip to.
        (dict) user_data: A dict containing the username and password
    """
    if zip_url is None:
        iface.messageBar().pushMessage("Error", "The json has no zip url.", level=QgsMessageBar.CRITICAL, duration=0)
        return
    else:
        data = open(os.path.join(temp_dir, "{}.zip".format(project_name))).read()
        encoded_user = base64.b64encode(user_data)
        req = urllib2.Request(zip_url, data, encoded_user)
        response = urllib2.urlopen(req)
        the_page = reponse.read()  # nodig