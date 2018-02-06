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

import json
import osgeo.ogr as ogr
import osgeo.osr as osr
import os
import shutil

from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtCore import Qt
from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QFileDialog
# from qgis.core import QgsMapLayerRegistry
from qgis.gui import QgsMessageBar
from qgis.utils import iface

# from beoordelingstool_dockwidget import BeoordelingstoolDockWidget

BUTTON_DOWNLOAD_RIOOL = "download_riool_search"
TEXTBOX_DOWNLOAD_RIOOL = "download_riool_text"
# from .utils.constants import BUTTON_DOWNLOAD_PUTTEN
# from .utils.constants import TEXTBOX_DOWNLOAD_PUTTEN
FILE_TYPE_JSON = "json"
# HERSTELMAATREGEL_DEFAULT = 1
# from .utils.constants import FILE_TYPE_JSON
# from .utils.get_data import get_file

LAYER_STYLES_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'layer_styles'))

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
        # Get json
        self.download_riool_search.clicked.connect(self.search_json_riool)
        # Save json in 3 shapefiles: manholes, pipes and measuring_points
        self.save_shapefiles_button.clicked.connect(
            self.save_shapefiles)
        # # Show dockwidget after pressing OK with all 3 layers
        # self.accepted.connect(self.show_dockwidget)

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

    def save_shapefiles(self):
        """Save the manholes, pipes and measuring stations shapefiles."""
        directory = self.get_shapefiles_directory()

        # Get json
        filename_json = self.download_riool_text.text()
        manholes, pipes = self.get_json(filename_json)

        self.save_shapefile_manholes(directory, manholes)
        self.save_shapefiles_pipes_measuringpoints(directory, pipes)

    def get_shapefiles_directory(self):
        """Get the directory to save the shapefiles in."""
        settings = QSettings('beoordelingstool', 'qgisplugin')

        try:
            init_path = settings.value('last_used_import_path', type=str)
        except TypeError:
            init_path = os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(None,
                                                     'Select directory',
                                                     init_path)

        if directory:
            settings.setValue('last_used_import_path',
                              os.path.dirname(directory))

        return str(directory)

    def save_shapefile_manholes(self, directory, manholes):
        """
        Function to save the manholes of the json.
        This function also shows the shapefile on the map.

        Args:
            (str) directory: The directory to save the shapefiles in.
            (json) manholes: The manholes to save in the shapefile.
        """

        # Manholes path
        manholes_path = os.path.join(directory, "manholes.shp")

        # Create manhole shapefile
        driver = ogr.GetDriverByName("ESRI Shapefile")
        data_source = driver.CreateDataSource(manholes_path)
        srs = osr.SpatialReference()
        # manholes[0]["CRS"]  # "Netherlands-RD"
        srs.ImportFromEPSG(28992)  # 4326  4289 RIBx 3857 GoogleMaps
        layer = data_source.CreateLayer(manholes_path, srs, ogr.wkbPoint)
        layer = self.fields_to_manholes_shp(layer, manholes)
        for manhole in manholes:
            layer = self.feature_to_manholes_shp(layer, manhole)
        data_source = None
        # Copy qml as layer style
        shutil.copyfile(os.path.abspath(os.path.join(LAYER_STYLES_DIR, "manholes.qml")), os.path.abspath(os.path.join(directory, "manholes.qml")))
        layer = iface.addVectorLayer(manholes_path, "manholes", "ogr")

    def save_shapefiles_pipes_measuringpoints(self, directory, pipes):
        """
        Function to save the pipes of the json.
        This function also shows this shapefile on the map.

        Args:
            (str) directory: The directory to save the shapefiles in.
            (json) pipes: The pipes to save in the shapefiles.
                The pipes json can have nested assets, known as measuring
                    stations.
        """
        
        # Pipes path
        pipes_path = os.path.join(directory, "pipes.shp")
        # Create pipes shapefile
        driver = ogr.GetDriverByName("ESRI Shapefile")
        data_source = driver.CreateDataSource(pipes_path)
        srs = osr.SpatialReference()
        # pipes[0]["Beginpunt CRS"]  # "Netherlands-RD"
        srs.ImportFromEPSG(28992)  # 4326  4289 RIBx 3857 GoogleMaps
        layer = data_source.CreateLayer(pipes_path, srs, ogr.wkbLineString)
        # data_source = None

        # Measuring points path
        measuring_points_path = os.path.join(directory, "measuring_points.shp")
        # Create measuring points shapefile
        driver = ogr.GetDriverByName("ESRI Shapefile")
        data_source_measuring_point = driver.CreateDataSource(measuring_points_path)
        srs = osr.SpatialReference()
        # pipes[0]["Beginpunt CRS"]  # "Netherlands-RD"
        srs.ImportFromEPSG(28992)  # 4326  4289 RIBx 3857 GoogleMaps
        measuring_points_layer = data_source_measuring_point.CreateLayer(measuring_points_path, srs, ogr.wkbPoint)

        # Populate pipe shapefile
        layer = self.fields_to_pipes_shp(layer, pipes)
        measuring_points_layer = self.fields_to_measuring_points_shp(measuring_points_layer)
        pipe_id = 0
        for pipe in pipes:  # add iterator for populating ID field
            layer = self.feature_to_pipes_shp(layer, pipe_id, pipe)  # add measuring points layer to save measuring points in if there are any
            if pipe["ZC"]:
                for measuring_point in pipe["ZC"]:
                    measuring_points_layer = self.feature_to_measuring_points_shp(measuring_points_layer, pipe_id, measuring_point)
            pipe_id += 1
        data_source = None
        # Copy qml as layer style
        shutil.copyfile(os.path.abspath(os.path.join(LAYER_STYLES_DIR, "pipes.qml")), os.path.abspath(os.path.join(directory, "pipes.qml")))
        layer = iface.addVectorLayer(pipes_path, "pipes", "ogr")

        data_source_measuring_point = None
        # Copy qml as layer style
        shutil.copyfile(os.path.abspath(os.path.join(LAYER_STYLES_DIR, "measuring_points.qml")), os.path.abspath(os.path.join(directory, "measuring_points.qml")))
        measuring_points_layer = iface.addVectorLayer(measuring_points_path, "measuring_points", "ogr")


    def get_json(self, filename):
        """Function to get a JSON."""
        manholes = []
        pipes = []
        with open(filename) as json_file:
            json_data = json.load(json_file)
            for manhole in json_data["manholes"]:
                manholes.append(manhole)
            for pipe in json_data["pipes"]:
                pipes.append(pipe)
        return (manholes, pipes)

    def fields_to_manholes_shp(self, layer, location):
        """
        Add fields to a shapefile layer.

        Args:
            (shapefile layer) layer: A shapefile layer.
            (shapefile layer) location: A shapefile layer.

        Returns:
            (shapefile layer) layer: A shapefile layer.
        """
        CAA = ogr.FieldDefn("CAA", ogr.OFTString)
        CAA.SetWidth(255)
        layer.CreateField(CAA)
        CAJ = ogr.FieldDefn("CAJ", ogr.OFTString)
        CAJ.SetWidth(255)
        layer.CreateField(CAJ)
        CAL = ogr.FieldDefn("CAL", ogr.OFTString)
        CAL.SetWidth(255)
        layer.CreateField(CAL)
        CAM = ogr.FieldDefn("CAM", ogr.OFTString)
        CAM.SetWidth(255)
        layer.CreateField(CAM)
        CAN = ogr.FieldDefn("CAN", ogr.OFTString)
        CAN.SetWidth(255)
        layer.CreateField(CAN)
        CAO = ogr.FieldDefn("CAO", ogr.OFTString)
        CAO.SetWidth(255)
        layer.CreateField(CAO)
        CAQ = ogr.FieldDefn("CAQ", ogr.OFTString)
        CAQ.SetWidth(255)
        layer.CreateField(CAQ)
        CAR = ogr.FieldDefn("CAR", ogr.OFTString)
        CAR.SetWidth(255)
        layer.CreateField(CAR)
        CBA = ogr.FieldDefn("CBA", ogr.OFTString)
        CBA.SetWidth(255)
        layer.CreateField(CBA)
        CBB = ogr.FieldDefn("CBB", ogr.OFTString)
        CBB.SetWidth(255)
        layer.CreateField(CBB)
        CBC = ogr.FieldDefn("CBC", ogr.OFTString)
        CBC.SetWidth(255)
        layer.CreateField(CBC)
        CBD = ogr.FieldDefn("CBD", ogr.OFTString)
        CBD.SetWidth(255)
        layer.CreateField(CBD)
        CBE = ogr.FieldDefn("CBE", ogr.OFTString)
        CBE.SetWidth(255)
        layer.CreateField(CBE)
        CBF = ogr.FieldDefn("CBF", ogr.OFTString)
        CBF.SetWidth(255)
        layer.CreateField(CBF)
        CBH = ogr.FieldDefn("CBH", ogr.OFTString)
        CBH.SetWidth(255)
        layer.CreateField(CBH)
        CBI = ogr.FieldDefn("CBI", ogr.OFTString)
        CBI.SetWidth(255)
        layer.CreateField(CBI)
        CBJ = ogr.FieldDefn("CBJ", ogr.OFTString)
        CBJ.SetWidth(255)
        layer.CreateField(CBJ)
        CBK = ogr.FieldDefn("CBK", ogr.OFTString)
        CBK.SetWidth(255)
        layer.CreateField(CBK)
        CBL = ogr.FieldDefn("CBL", ogr.OFTString)
        CBL.SetWidth(255)
        layer.CreateField(CBL)
        CBM = ogr.FieldDefn("CBM", ogr.OFTString)
        CBM.SetWidth(255)
        layer.CreateField(CBM)
        CBO = ogr.FieldDefn("CBO", ogr.OFTString)
        CBO.SetWidth(255)
        layer.CreateField(CBO)
        CBP = ogr.FieldDefn("CBP", ogr.OFTString)
        CBP.SetWidth(255)
        layer.CreateField(CBP)
        CCA = ogr.FieldDefn("CCA", ogr.OFTString)
        CCA.SetWidth(255)
        layer.CreateField(CCA)
        CCB = ogr.FieldDefn("CCB", ogr.OFTString)
        CCB.SetWidth(255)
        layer.CreateField(CCB)
        CCC = ogr.FieldDefn("CCC", ogr.OFTString)
        CCC.SetWidth(255)
        layer.CreateField(CCC)
        CCD = ogr.FieldDefn("CCD", ogr.OFTString)
        CCD.SetWidth(255)
        layer.CreateField(CCD)
        CCK = ogr.FieldDefn("CCK", ogr.OFTString)
        CCK.SetWidth(255)
        layer.CreateField(CCK)
        CCM = ogr.FieldDefn("CCM", ogr.OFTString)
        CCM.SetWidth(255)
        layer.CreateField(CCM)
        CCN = ogr.FieldDefn("CCN", ogr.OFTString)
        CCN.SetWidth(255)
        layer.CreateField(CCN)
        CCO = ogr.FieldDefn("CCO", ogr.OFTString)
        CCO.SetWidth(255)
        layer.CreateField(CCO)
        CCP = ogr.FieldDefn("CCP", ogr.OFTString)
        CCP.SetWidth(255)
        layer.CreateField(CCP)
        CCQ = ogr.FieldDefn("CCQ", ogr.OFTString)
        CCQ.SetWidth(255)
        layer.CreateField(CCQ)
        CCR = ogr.FieldDefn("CCR", ogr.OFTString)
        CCR.SetWidth(255)
        layer.CreateField(CCR)
        CCS = ogr.FieldDefn("CCS", ogr.OFTString)
        CCS.SetWidth(255)
        layer.CreateField(CCS)
        CDA = ogr.FieldDefn("CDA", ogr.OFTString)
        CDA.SetWidth(255)
        layer.CreateField(CDA)
        CDB = ogr.FieldDefn("CDB", ogr.OFTString)
        CDB.SetWidth(255)
        layer.CreateField(CDB)
        CDC = ogr.FieldDefn("CDC", ogr.OFTString)
        CDC.SetWidth(255)
        layer.CreateField(CDC)
        CDD = ogr.FieldDefn("CDD", ogr.OFTString)
        CDD.SetWidth(255)
        layer.CreateField(CDD)
        herstelmaatregel = ogr.FieldDefn("Herstelmaa", ogr.OFTString)
        herstelmaatregel.SetWidth(255)
        layer.CreateField(herstelmaatregel)
        opmerking = ogr.FieldDefn("Opmerking", ogr.OFTString)
        opmerking.SetWidth(255)
        layer.CreateField(opmerking)
        return layer

    def feature_to_manholes_shp(self, layer, manhole):
        """
        Add features to a shapefile.

        Args:
            (shapefile layer) layer: A shapefile layer.
            (dict) queryset: A Django queryset that will be used for getting
                the values of the fields.

        Returns:
            (shapefile layer) layer: A shapefile layer.
        """
        # Get values
        CAA = manhole["CAA"]
        x = manhole["x"]
        y = manhole["y"]
        CAJ = manhole["CAJ"]
        CAL = manhole["CAL"]
        CAM = manhole["CAM"]
        CAN = manhole["CAN"]
        CAO = manhole["CAO"]
        CAQ = manhole["CAQ"]
        CAR = manhole["CAR"]
        CBA = manhole["CBA"]
        CBB = manhole["CBB"]
        CBC = manhole["CBC"]
        CBD = manhole["CBD"]
        CBE = manhole["CBE"]
        CBF = manhole["CBF"]
        CBH = manhole["CBH"]
        CBI = manhole["CBI"]
        CBJ = manhole["CBJ"]
        CBK = manhole["CBK"]
        CBL = manhole["CBL"]
        CBM = manhole["CBM"]
        CBO = manhole["CBO"]
        CBP = manhole["CBP"]
        CCA = manhole["CCA"]
        CCB = manhole["CCB"]
        CCC = manhole["CCC"]
        CCD = manhole["CCD"]
        CCK = manhole["CCK"]
        CCM = manhole["CCM"]
        CCN = manhole["CCN"]
        CCO = manhole["CCO"]
        CCP = manhole["CCP"]
        CCQ = manhole["CCQ"]
        CCR = manhole["CCR"]
        CCS = manhole["CCS"]
        CDA = manhole["CDA"]
        CDB = manhole["CDB"]
        CDC = manhole["CDC"]
        CDD = manhole["CDD"]
        herstelmaatregel = manhole["Herstelmaatregel"]
        # herstelmaatregel = HERSTELMAATREGEL_DEFAULT
        opmerking = manhole["Opmerking"]

        # Set values
        feature = ogr.Feature(layer.GetLayerDefn())
        wkt = "POINT({} {})".format(x, y)
        point = ogr.CreateGeometryFromWkt(wkt)
        feature.SetGeometry(point)
        feature.SetField("CAA", str(CAA))
        feature.SetField("CAJ", str(CAJ))
        feature.SetField("CAL", str(CAL))
        feature.SetField("CAM", str(CAM))
        feature.SetField("CAN", str(CAN))
        feature.SetField("CAO", str(CAO))
        feature.SetField("CAQ", str(CAQ))
        feature.SetField("CAR", str(CAR))
        feature.SetField("CBA", str(CBA))
        feature.SetField("CBB", str(CBB))
        feature.SetField("CBC", str(CBC))
        feature.SetField("CBD", str(CBD))
        feature.SetField("CBE", str(CBE))
        feature.SetField("CBF", str(CBF))
        feature.SetField("CBH", str(CBH))
        feature.SetField("CBI", str(CBI))
        feature.SetField("CBJ", str(CBJ))
        feature.SetField("CBK", str(CBK))
        feature.SetField("CBL", str(CBL))
        feature.SetField("CBM", str(CBM))
        feature.SetField("CBO", str(CBO))
        feature.SetField("CBP", str(CBP))
        feature.SetField("CCA", str(CCA))
        feature.SetField("CCB", str(CCB))
        feature.SetField("CCC", str(CCC))
        feature.SetField("CCD", str(CCD))
        feature.SetField("CCK", str(CCK))
        feature.SetField("CCM", str(CCM))
        feature.SetField("CCN", str(CCN))
        feature.SetField("CCO", str(CCO))
        feature.SetField("CCP", str(CCP))
        feature.SetField("CCQ", str(CCQ))
        feature.SetField("CCR", str(CCR))
        feature.SetField("CCS", str(CCS))
        feature.SetField("CDA", str(CDA))
        feature.SetField("CDB", str(CDB))
        feature.SetField("CDC", str(CDC))
        feature.SetField("CDD", str(CDD))
        feature.SetField("Herstelmaa", str(herstelmaatregel))
        feature.SetField("Opmerking", str(opmerking))
        layer.CreateFeature(feature)

        feature = None
        return layer

    def fields_to_pipes_shp(self, layer, location):
        """
        Add fields to a shapefile layer.

        Args:
            (shapefile layer) layer: A shapefile layer.
            (shapefile layer) location: A shapefile layer.

        Returns:
            (shapefile layer) layer: A shapefile layer.
        """
        ID = ogr.FieldDefn("ID", ogr.OFTString)
        ID.SetWidth(255)
        layer.CreateField(ID)
        AAA = ogr.FieldDefn("AAA", ogr.OFTString)
        AAA.SetWidth(255)
        layer.CreateField(AAA)
        AAB = ogr.FieldDefn("AAB", ogr.OFTString)
        AAB.SetWidth(255)
        layer.CreateField(AAB)
        AAD = ogr.FieldDefn("AAD", ogr.OFTString)
        AAD.SetWidth(255)
        layer.CreateField(AAD)
        AAE = ogr.FieldDefn("AAE", ogr.OFTString)
        AAE.SetWidth(255)
        layer.CreateField(AAE)
        AAF = ogr.FieldDefn("AAF", ogr.OFTString)
        AAF.SetWidth(255)
        layer.CreateField(AAF)
        AAG = ogr.FieldDefn("AAG", ogr.OFTString)
        AAG.SetWidth(255)
        layer.CreateField(AAG)
        AAJ = ogr.FieldDefn("AAJ", ogr.OFTString)
        AAJ.SetWidth(255)
        layer.CreateField(AAJ)
        AAK = ogr.FieldDefn("AAK", ogr.OFTString)
        AAK.SetWidth(255)
        layer.CreateField(AAK)
        AAL = ogr.FieldDefn("AAL", ogr.OFTString)
        AAL.SetWidth(255)
        layer.CreateField(AAL)
        AAM = ogr.FieldDefn("AAM", ogr.OFTString)
        AAM.SetWidth(255)
        layer.CreateField(AAM)
        AAN = ogr.FieldDefn("AAN", ogr.OFTString)
        AAN.SetWidth(255)
        layer.CreateField(AAN)
        AAO = ogr.FieldDefn("AAO", ogr.OFTString)
        AAO.SetWidth(255)
        layer.CreateField(AAO)
        AAP = ogr.FieldDefn("AAP", ogr.OFTString)
        AAP.SetWidth(255)
        layer.CreateField(AAP)
        AAQ = ogr.FieldDefn("AAQ", ogr.OFTString)
        AAQ.SetWidth(255)
        layer.CreateField(AAQ)
        ABA = ogr.FieldDefn("ABA", ogr.OFTString)
        ABA.SetWidth(255)
        layer.CreateField(ABA)
        ABB = ogr.FieldDefn("ABB", ogr.OFTString)
        ABB.SetWidth(255)
        layer.CreateField(ABB)
        ABC = ogr.FieldDefn("ABC", ogr.OFTString)
        ABC.SetWidth(255)
        layer.CreateField(ABC)
        ABE = ogr.FieldDefn("ABE", ogr.OFTString)
        ABE.SetWidth(255)
        layer.CreateField(ABE)
        ABF = ogr.FieldDefn("ABF", ogr.OFTString)
        ABF.SetWidth(255)
        layer.CreateField(ABF)
        ABH = ogr.FieldDefn("ABH", ogr.OFTString)
        ABH.SetWidth(255)
        layer.CreateField(ABH)
        ABI = ogr.FieldDefn("ABI", ogr.OFTString)
        ABI.SetWidth(255)
        layer.CreateField(ABI)
        ABJ = ogr.FieldDefn("ABJ", ogr.OFTString)
        ABJ.SetWidth(255)
        layer.CreateField(ABJ)
        ABK = ogr.FieldDefn("ABK", ogr.OFTString)
        ABK.SetWidth(255)
        layer.CreateField(ABK)
        ABL = ogr.FieldDefn("ABL", ogr.OFTString)
        ABL.SetWidth(255)
        layer.CreateField(ABL)
        ABM = ogr.FieldDefn("ABM", ogr.OFTString)
        ABM.SetWidth(255)
        layer.CreateField(ABM)
        ABP = ogr.FieldDefn("ABP", ogr.OFTString)
        ABP.SetWidth(255)
        layer.CreateField(ABP)
        ABQ = ogr.FieldDefn("ABQ", ogr.OFTString)
        ABQ.SetWidth(255)
        layer.CreateField(ABQ)
        ABS = ogr.FieldDefn("ABS", ogr.OFTString)
        ABS.SetWidth(255)
        layer.CreateField(ABS)
        ACA = ogr.FieldDefn("ACA", ogr.OFTString)
        ACA.SetWidth(255)
        layer.CreateField(ACA)
        ACB = ogr.FieldDefn("ACB", ogr.OFTString)
        ACB.SetWidth(255)
        layer.CreateField(ACB)
        ACC = ogr.FieldDefn("ACC", ogr.OFTString)
        ACC.SetWidth(255)
        layer.CreateField(ACC)
        ACD = ogr.FieldDefn("ACD", ogr.OFTString)
        ACD.SetWidth(255)
        layer.CreateField(ACD)
        ACG = ogr.FieldDefn("ACG", ogr.OFTString)
        ACG.SetWidth(255)
        layer.CreateField(ACG)
        ACJ = ogr.FieldDefn("ACJ", ogr.OFTString)
        ACJ.SetWidth(255)
        layer.CreateField(ACJ)
        ACK = ogr.FieldDefn("ACK", ogr.OFTString)
        ACK.SetWidth(255)
        layer.CreateField(ACK)
        ACM = ogr.FieldDefn("ACM", ogr.OFTString)
        ACM.SetWidth(255)
        layer.CreateField(ACM)
        ACN = ogr.FieldDefn("ACN", ogr.OFTString)
        ACN.SetWidth(255)
        layer.CreateField(ACN)
        ADA = ogr.FieldDefn("ADA", ogr.OFTString)
        ADA.SetWidth(255)
        layer.CreateField(ADA)
        ADB = ogr.FieldDefn("ADB", ogr.OFTString)
        ADB.SetWidth(255)
        layer.CreateField(ADB)
        ADC = ogr.FieldDefn("ADC", ogr.OFTString)
        ADC.SetWidth(255)
        layer.CreateField(ADC)
        AXA = ogr.FieldDefn("AXA", ogr.OFTString)
        AXA.SetWidth(255)
        layer.CreateField(AXA)
        AXB = ogr.FieldDefn("AXB", ogr.OFTString)
        AXB.SetWidth(255)
        layer.CreateField(AXB)
        AXF = ogr.FieldDefn("AXF", ogr.OFTString)
        AXF.SetWidth(255)
        layer.CreateField(AXF)
        AXG = ogr.FieldDefn("AXG", ogr.OFTString)
        AXG.SetWidth(255)
        layer.CreateField(AXG)
        AXH = ogr.FieldDefn("AXH", ogr.OFTString)
        AXH.SetWidth(255)
        layer.CreateField(AXH)
        ZC = ogr.FieldDefn("ZC", ogr.OFTString)
        ZC.SetWidth(255)
        layer.CreateField(ZC)
        herstelmaatregel = ogr.FieldDefn("Herstelmaa", ogr.OFTString)
        herstelmaatregel.SetWidth(255)
        layer.CreateField(herstelmaatregel)
        opmerking = ogr.FieldDefn("Opmerking", ogr.OFTString)
        opmerking.SetWidth(255)
        layer.CreateField(opmerking)
        return layer

    def feature_to_pipes_shp(self, layer, id_nr, pipe):
        """
        Add features to a shapefile.

        Args:
            (shapefile layer) layer: A shapefile layer.
            (dict) queryset: A Django queryset that will be used for getting
                the values of the fields.

        Returns:
            (shapefile layer) layer: A shapefile layer.
        """
        # Get values
        id_nr = id_nr
        start_x = pipe["Beginpunt x"]
        start_y = pipe["Beginpunt y"]
        end_x = pipe["Eindpunt x"]
        end_y = pipe["Eindpunt y"]
        AAA = pipe["AAA"]
        AAB = pipe["AAB"]
        AAD = pipe["AAD"]
        AAE = pipe["AAE"]
        AAF = pipe["AAF"]
        AAG = pipe["AAG"]
        AAJ = pipe["AAJ"]
        AAK = pipe["AAK"]
        AAL = pipe["AAL"]
        AAM = pipe["AAM"]
        AAN = pipe["AAN"]
        AAO = pipe["AAO"]
        AAP = pipe["AAP"]
        AAQ = pipe["AAQ"]
        ABA = pipe["ABA"]
        ABB = pipe["ABB"]
        ABC = pipe["ABC"]
        ABE = pipe["ABE"]
        ABF = pipe["ABF"]
        ABH = pipe["ABH"]
        ABI = pipe["ABI"]
        ABJ = pipe["ABJ"]
        ABK = pipe["ABK"]
        ABL = pipe["ABL"]
        ABM = pipe["ABM"]
        ABP = pipe["ABP"]
        ABQ = pipe["ABQ"]
        ABS = pipe["ABS"]
        ACA = pipe["ACA"]
        ACB = pipe["ACB"]
        ACC = pipe["ACC"]
        ACD = pipe["ACD"]
        ACG = pipe["ACG"]
        ACJ = pipe["ACJ"]
        ACK = pipe["ACK"]
        ACM = pipe["ACM"]
        ACN = pipe["ACN"]
        ADA = pipe["ADA"]
        ADB = pipe["ADB"]
        ADC = pipe["ADC"]
        AXA = pipe["AXA"]
        AXB = pipe["AXB"]
        AXF = pipe["AXF"]
        AXG = pipe["AXG"]
        AXH = pipe["AXH"]
        ZC = pipe["ZC"]
        herstelmaatregel = pipe["Herstelmaatregel"]
        # herstelmaatregel = HERSTELMAATREGEL_DEFAULT
        opmerking = pipe["Opmerking"]

        # Set values
        feature = ogr.Feature(layer.GetLayerDefn())
        wkt = "LINESTRING({} {}, {} {})".format(start_x, start_y, end_x, end_y)
        line = ogr.CreateGeometryFromWkt(wkt)
        feature.SetGeometry(line)
        feature.SetField("ID", str(id_nr))
        feature.SetField("AAA", str(AAA))
        feature.SetField("AAB", str(AAB))
        feature.SetField("AAD", str(AAD))
        feature.SetField("AAE", str(AAE))
        feature.SetField("AAF", str(AAF))
        feature.SetField("AAG", str(AAG))
        feature.SetField("AAJ", str(AAJ))
        feature.SetField("AAK", str(AAK))
        feature.SetField("AAL", str(AAL))
        feature.SetField("AAM", str(AAM))
        feature.SetField("AAN", str(AAN))
        feature.SetField("AAO", str(AAO))
        feature.SetField("AAP", str(AAP))
        feature.SetField("AAQ", str(AAQ))
        feature.SetField("ABA", str(ABA))
        feature.SetField("ABB", str(ABB))
        feature.SetField("ABC", str(ABC))
        feature.SetField("ABE", str(ABE))
        feature.SetField("ABF", str(ABF))
        feature.SetField("ABH", str(ABH))
        feature.SetField("ABI", str(ABI))
        feature.SetField("ABJ", str(ABJ))
        feature.SetField("ABK", str(ABK))
        feature.SetField("ABL", str(ABL))
        feature.SetField("ABM", str(ABM))
        feature.SetField("ABP", str(ABP))
        feature.SetField("ABQ", str(ABQ))
        feature.SetField("ABS", str(ABS))
        feature.SetField("ACA", str(ACA))
        feature.SetField("ACB", str(ACB))
        feature.SetField("ACC", str(ACC))
        feature.SetField("ACD", str(ACD))
        feature.SetField("ACG", str(ACG))
        feature.SetField("ACJ", str(ACJ))
        feature.SetField("ACK", str(ACK))
        feature.SetField("ACM", str(ACM))
        feature.SetField("ACN", str(ACN))
        feature.SetField("ADA", str(ADA))
        feature.SetField("ADB", str(ADB))
        feature.SetField("ADC", str(ADC))
        feature.SetField("AXA", str(AXA))
        feature.SetField("AXB", str(AXB))
        feature.SetField("AXF", str(AXF))
        feature.SetField("AXG", str(AXG))
        feature.SetField("AXH", str(AXH))
        feature.SetField("ZC", str(ZC))
        feature.SetField("Herstelmaa", str(herstelmaatregel))
        feature.SetField("Opmerking", str(opmerking))
        layer.CreateFeature(feature)

        feature = None
        return layer

    def fields_to_measuring_points_shp(self, layer):
        """
        Add fields to a shapefile layer.

        Args:
            (shapefile layer) layer: A shapefile layer.
            (shapefile layer) location: A shapefile layer.

        Returns:
            (shapefile layer) layer: A shapefile layer.
        """
        PIPES_ID = ogr.FieldDefn("PIPE_ID", ogr.OFTString)
        PIPES_ID.SetWidth(255)
        layer.CreateField(PIPES_ID)
        x = ogr.FieldDefn("x", ogr.OFTString)
        x.SetWidth(255)
        layer.CreateField(x)
        y = ogr.FieldDefn("y", ogr.OFTString)
        y.SetWidth(255)
        layer.CreateField(y)
        A = ogr.FieldDefn("A", ogr.OFTString)
        A.SetWidth(255)
        layer.CreateField(A)
        B = ogr.FieldDefn("B", ogr.OFTString)
        B.SetWidth(255)
        layer.CreateField(B)
        C = ogr.FieldDefn("C", ogr.OFTString)
        C.SetWidth(255)
        layer.CreateField(C)
        D = ogr.FieldDefn("D", ogr.OFTString)
        D.SetWidth(255)
        layer.CreateField(D)
        E = ogr.FieldDefn("E", ogr.OFTString)
        E.SetWidth(255)
        layer.CreateField(E)
        F = ogr.FieldDefn("F", ogr.OFTString)
        F.SetWidth(255)
        layer.CreateField(F)
        G = ogr.FieldDefn("G", ogr.OFTString)
        G.SetWidth(255)
        layer.CreateField(G)
        I = ogr.FieldDefn("I", ogr.OFTString)
        I.SetWidth(255)
        layer.CreateField(I)
        J = ogr.FieldDefn("J", ogr.OFTString)
        J.SetWidth(255)
        layer.CreateField(J)
        K = ogr.FieldDefn("K", ogr.OFTString)
        K.SetWidth(255)
        layer.CreateField(K)
        M = ogr.FieldDefn("M", ogr.OFTString)
        M.SetWidth(255)
        layer.CreateField(M)
        N = ogr.FieldDefn("N", ogr.OFTString)
        N.SetWidth(255)
        layer.CreateField(N)
        O = ogr.FieldDefn("O", ogr.OFTString)
        O.SetWidth(255)
        layer.CreateField(O)
        herstelmaatregel = ogr.FieldDefn("Herstelmaa", ogr.OFTString)
        herstelmaatregel.SetWidth(255)
        layer.CreateField(herstelmaatregel)
        opmerking = ogr.FieldDefn("Opmerking", ogr.OFTString)
        opmerking.SetWidth(255)
        layer.CreateField(opmerking)
        return layer

    def feature_to_measuring_points_shp(self, layer, pipe_id, measuring_point):
        """
        Add features to a shapefile.

        Args:
            (shapefile layer) layer: A shapefile layer.
            (dict) queryset: A Django queryset that will be used for getting
                the values of the fields.

        Returns:
            (shapefile layer) layer: A shapefile layer.
        """
        # Get values
        x = measuring_point["x"] if measuring_point["x"] else 0.0
        y = measuring_point["y"] if measuring_point["y"] else 0.0
        A = measuring_point.get("A", None)
        B = measuring_point.get("B", None)
        C = measuring_point.get("C", None)
        D = measuring_point.get("D", None)
        E = measuring_point.get("E", None)
        F = measuring_point.get("F", None)
        G = measuring_point.get("G", None)
        I = measuring_point.get("I", None)
        J = measuring_point.get("J", None)
        K = measuring_point.get("K", None)
        M = measuring_point.get("M", None)
        N = measuring_point.get("N", None)
        O = measuring_point.get("O", None)
        herstelmaatregel = measuring_point["Herstelmaatregel"] if measuring_point["Herstelmaatregel"] else 1
        # herstelmaatregel = HERSTELMAATREGEL_DEFAULT
        opmerking = measuring_point["Opmerking"] if measuring_point["Opmerking"] else ""

        # Set values
        feature = ogr.Feature(layer.GetLayerDefn())
        wkt = "POINT({} {})".format(x, y)
        point = ogr.CreateGeometryFromWkt(wkt)
        feature.SetGeometry(point)
        feature.SetField("PIPE_ID", str(pipe_id))
        feature.SetField("x", str(x))
        feature.SetField("y", str(y))
        feature.SetField("A", str(A))
        feature.SetField("B", str(B))
        feature.SetField("C", str(C))
        feature.SetField("D", str(D))
        feature.SetField("E", str(E))
        feature.SetField("F", str(F))
        feature.SetField("G", str(G))
        feature.SetField("I", str(I))
        feature.SetField("J", str(J))
        feature.SetField("K", str(K))
        feature.SetField("M", str(M))
        feature.SetField("N", str(N))
        feature.SetField("O", str(O))
        feature.SetField("Herstelmaa", str(herstelmaatregel))
        feature.SetField("Opmerking", str(opmerking))
        layer.CreateFeature(feature)

        feature = None
        return layer

    # def show_dockwidget(self):
    #     """Show the dockwidget if all 3 layers exist."""
    #     manholes_layerList = QgsMapLayerRegistry.instance().mapLayersByName("manholes")
    #     pipes_layerList = QgsMapLayerRegistry.instance().mapLayersByName("pipes")
    #     measuring_stations_layerList = QgsMapLayerRegistry.instance().mapLayersByName("measuring_points")

    #     if manholes_layerList or pipes_layerList or measuring_stations_layerList:
    #         # dockwidget = BeoordelingstoolDockWidget()
    #         # dockwidget.closingPlugin.connect(dockwidget.closeEvent)
    #         # iface.addDockWidget(Qt.RightDockWidgetArea, dockwidget)
    #         # dockwidget.show()
