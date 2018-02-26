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
from PyQt4.QtGui import QDesktopServices
from qgis.core import QgsExpression
from qgis.core import QgsFeatureRequest
from qgis.core import QgsMapLayerRegistry
from qgis.gui import QgsMessageBar
from qgis.utils import iface

from beoordelingstool_download_dialog import BeoordelingstoolDownloadDialog
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
