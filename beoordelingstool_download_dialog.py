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
from qgis.core import QgsMapLayerRegistry
from qgis.gui import QgsMessageBar
from qgis.utils import iface

from .utils.constants import FILE_TYPE_JSON
from .utils.constants import JSON_NAME
from .utils.constants import SHP_NAME_MANHOLES
from .utils.constants import SHP_NAME_PIPES
from .utils.constants import SHP_NAME_MEASURING_POINTS
from .utils.constants import ZB_A_FIELDS
from .utils.constants import ZB_C_FIELDS

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
        self.accepted.connect(self.check_for_existing_shapefiles)
        # Show dockwidget after pressing OK with all 3 layers
        self.json_path = ''
        self.directory = ""

    def closeEvent(self, event):
        # self.closingPlugin.emit()
        # event.accept()
        pass

    def search_json_riool(self):
        """Get the json of 'Rioolputten'."""
        file_type = FILE_TYPE_JSON
        self.search_file(file_type)

    def search_file(self, file_type):
        """
        Function to search a file.

        Args:
            (str) file_type: The type of file.
        """
        filename = self.get_file(file_type)
        self.json_path = filename

    def get_file(self, file_type):
        """
        Function to get a file.

        Args:
            (str) file_type: The type of file.
        """
        settings = QSettings('beoordelingstool', 'qgisplugin')

        try:
            init_path = settings.value('last_used_import_path', type=str)
        except TypeError:
            init_path = os.path.expanduser("~")
        if file_type == FILE_TYPE_JSON:
            filename = QFileDialog.getOpenFileName(None,
                                                   'Open json file',
                                                   init_path,
                                                   'JSON (*.json)')

        if filename:
            settings.setValue('last_used_import_path',
                              os.path.dirname(filename))

        return filename

    def check_for_existing_shapefiles(self):
        """
        Check whether the json, direcotry and shapefiles already exist.
        If the shapefiles exist, let the user choose to overwrite them
        with the BeoordelingstoolOverwriteShapefilesDialog.
        """
        if self.json_path != '':
            self.directory = self.get_shapefiles_directory()
            manholes_path = os.path.join(self.directory, "{}.shp".format(SHP_NAME_MANHOLES))
            pipes_path = os.path.join(self.directory, "{}.shp".format(SHP_NAME_PIPES))
            measuring_stations_path = os.path.join(self.directory, "{}.shp".format(SHP_NAME_MEASURING_POINTS))

            if self.directory != '':
                if os.path.exists(manholes_path) or os.path.exists(pipes_path) or os.path.exists(pipes_path):
                    iface.messageBar().pushMessage("Warning", "Manholes, \
                    pipes or measuring stations shapefile already exists.",
                                                   level=QgsMessageBar.WARNING, duration=20)
                else:
                    self.save_shapefiles(overwrite_shapefiles=True)
            else:
                iface.messageBar()\
                     .pushMessage("Warning",
                                  "No shapefile directory found.",
                                  level=QgsMessageBar.WARNING, duration=0)
        else:
            iface.messageBar().pushMessage("Warning", "No json found.", level=QgsMessageBar.WARNING, duration=0)

    def get_shapefiles_directory(self):
        """
        Get the directory to save the shapefiles in.


        Returns:
            (string) directory: The absolute path to save the shapefiles in.
        """
        settings = QSettings('beoordelingstool', 'qgisplugin')

        try:
            init_path = settings.value('last_used_import_path', type=str)
        except TypeError:
            init_path = os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(None,
                                                     'Select directory for saving shapefiles',
                                                     init_path)

        if directory:
            settings.setValue('last_used_import_path',
                              os.path.dirname(directory))

        return str(directory)

    def get_overwrite_shapefiles(self, overwrite_shapefiles):
        """
        Get from the BeoordelingstoolOverwriteShapefilesDialog whether the
        user wants to overwrite existing shapefiles.

        Arguments:
            (boolean) overwrite_shapefiles: Whether the user wants to
                overwrite existing shapefiles.

        Returns:
            (boolean) overwrite_shapefiles: Whether the user wants to
                overwrite existing shapefiles.
        """
        print("Overwrite shapefiles: {}.".format(overwrite_shapefiles))
        self.save_shapefiles(overwrite_shapefiles)

    def save_shapefiles(self, overwrite_shapefiles=True):
        """
        Save the manholes, pipes and measuring stations shapefiles and show them as layers
        on the map.
        """
        if overwrite_shapefiles is True:
            # Get json
            filename_json = self.json_path
            manholes, pipes = self.get_json_manholes_and_pipes(filename_json)
            # Save json as review.json
            json_origin = os.path.abspath(self.json_path)
            json_dest = os.path.abspath(os.path.join(self.directory, JSON_NAME))
            if json_origin != json_dest:
                shutil.copyfile(os.path.abspath(json_origin), os.path.abspath(json_dest))
            # Save shapefiles
            self.save_shapefile_manholes(self.directory, manholes, overwrite_shapefiles)
            self.save_shapefiles_pipes_measuringpoints(self.directory, pipes, overwrite_shapefiles)
        show_shapefile_layers(self.directory)

    def get_json_manholes_and_pipes(self, filename):
        """
        Function to get a JSON.

        Arguments:
            (string) filename: The absolute path to the JSON.

        Returns:
            (tuple) manholes, pipes: A manhole containing manholes and pipes,
                both containing a JSON.
        """
        manholes = []
        pipes = []
        with open(filename) as json_file:
            json_data = json.load(json_file)
            for manhole in json_data["manholes"]:
                manholes.append(manhole)
            for pipe in json_data["pipes"]:
                pipes.append(pipe)
        return (manholes, pipes)

    def save_shapefile_manholes(self, directory, manholes, overwrite_shapefiles=False):
        """
        Function to save the manholes of the json.

        Args:
            (string) directory: The directory to save the shapefiles in.
            (json) manholes: The manholes to save in the shapefile.
            (boolean) overwrite_shapefiles: An optional parameter, telling
                whether or not possible existing shapefiles should be
                overwritten. The default is set to False, to not
                accidentally overwrite shapefiles.
        """
        # Manholes path
        manholes_filename = "{}.shp".format(SHP_NAME_MANHOLES)
        manholes_path = os.path.join(directory, manholes_filename)

        # Create manhole shapefile
        driver = ogr.GetDriverByName("ESRI Shapefile")
        # try /except for data_source?
        data_source = driver.CreateDataSource(directory)
        if data_source is None:
            if os.path.exists(manholes_path) or overwrite_shapefiles is True:
                try:
                    driver.DeleteDataSource(manholes_path)
                    print("{} deleted.".format(manholes_path))
                except Exception as e:
                    print("{} not found.".format(manholes_path))
            else:
                iface.messageBar()\
                     .pushMessage("Error",
                                  "Shapefiles already exist.",
                                  level=QgsMessageBar.CRITICAL, duration=0)  # does not say anythong to user
                return
        srs = osr.SpatialReference()
        # manholes[0]["CRS"]  # "Netherlands-RD"
        srs.ImportFromEPSG(28992)  # 4326  4289 RIBx 3857 GoogleMaps
        if os.path.exists(manholes_path) or overwrite_shapefiles is True:
            try:
                driver.DeleteDataSource(manholes_path)
                print("{} deleted.".format(manholes_path))
            except Exception as e:
                print "{} not found.".format(manholes_path)
        layer = data_source.CreateLayer(SHP_NAME_MANHOLES, srs, ogr.wkbPoint)
        layer = self.fields_to_manholes_shp(layer, manholes)
        for manhole in manholes:
            layer = self.feature_to_manholes_shp(layer, manhole)
        data_source = None
        # Copy qml as layer style
        shutil.copyfile(os.path.abspath(os.path.join(LAYER_STYLES_DIR, "{}.qml".format(SHP_NAME_MANHOLES))), os.path.abspath(os.path.join(directory, "{}.qml".format(SHP_NAME_MANHOLES))))

    def save_shapefiles_pipes_measuringpoints(self, directory, pipes, overwrite_shapefiles=False):
        """
        Function to save the pipes of the json.
        This function also shows this shapefile on the map.

        Args:
            (str) directory: The directory to save the shapefiles in.
            (json) pipes: The pipes to save in the shapefiles.
                The pipes json can have nested assets, known as measuring
                points.
            (boolean) overwrite_shapefiles: An optional parameter, telling
                whether or not possible existing shapefiles should be
                overwritten. The default is set to False, to not
                accidentally overwrite shapefiles.
        """

        # Pipes path
        pipes_filename = "{}.shp".format(SHP_NAME_PIPES)
        pipes_path = os.path.join(directory, pipes_filename)

        # Create pipes shapefile
        driver = ogr.GetDriverByName("ESRI Shapefile")
        # try:
        data_source = driver.CreateDataSource(directory)
        if data_source is None:
            if os.path.exists(pipes_path) or overwrite_shapefiles is True:
                try:
                    driver.DeleteDataSource(pipes_path)
                    print "{} deleted.".format(pipes_path)
                except Exception as e:
                    print "{} not found.".format(pipes_path)
            else:
                iface.messageBar().pushMessage("Error",
                                               "data_source is None.",
                                               level=QgsMessageBar.CRITICAL, duration=0)
                return
        srs = osr.SpatialReference()
        # pipes[0]["Beginpunt CRS"]  # "Netherlands-RD"
        srs.ImportFromEPSG(28992)
        if os.path.exists(pipes_path) or overwrite_shapefiles is True:
            try:
                driver.DeleteDataSource(pipes_path)
                print "{} deleted.".format(pipes_path)
            except Exception as e:
                print "{} not found.".format(pipes_path)
        layer = data_source.CreateLayer(SHP_NAME_PIPES, srs, ogr.wkbLineString)
        # data_source = None

        # Measuring points path
        measuring_points_filename = "{}.shp".format(SHP_NAME_MEASURING_POINTS)
        measuring_points_path = os.path.join(directory, measuring_points_filename)
        # Create measuring points shapefile
        driver = ogr.GetDriverByName("ESRI Shapefile")
        data_source_measuring_point = driver.CreateDataSource(directory)
        if data_source_measuring_point is None:
            if os.path.exists(measuring_points_path) or overwrite_shapefiles is True:
                try:
                    driver.DeleteDataSource(measuring_points_path)
                    print "{} deleted.".format(measuring_points_path)
                except Exception as e:
                    print "{} not found.".format(measuring_points_path)
            else:
                iface.messageBar()\
                      .pushMessage("Error", "data_source is None.",
                                   level=QgsMessageBar.CRITICAL, duration=0)  # does not say anythong to user
                return
        srs = osr.SpatialReference()
        # pipes[0]["Beginpunt CRS"]  # "Netherlands-RD"
        srs.ImportFromEPSG(28992)
        if os.path.exists(measuring_points_path) or overwrite_shapefiles is True:
            try:
                driver.DeleteDataSource(measuring_points_path)
                print "{} deleted.".format(measuring_points_path)
            except Exception as e:
                print "{} not found.".format(measuring_points_path)
        measuring_points_layer = data_source_measuring_point.CreateLayer(SHP_NAME_MEASURING_POINTS, srs, ogr.wkbPoint)

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
        shutil.copyfile(os.path.abspath(os.path.join(LAYER_STYLES_DIR, "{}.qml".format(SHP_NAME_PIPES))), os.path.abspath(os.path.join(directory, "{}.qml".format(SHP_NAME_PIPES))))

        data_source_measuring_point = None
        # Copy qml as layer style
        shutil.copyfile(os.path.abspath(os.path.join(LAYER_STYLES_DIR, "{}.qml".format(SHP_NAME_MEASURING_POINTS))), os.path.abspath(os.path.join(directory, "{}.qml".format(SHP_NAME_MEASURING_POINTS))))
        # except Exception as e:
        #     print e

    def fields_to_manholes_shp(self, layer, location):
        """
        Add fields to a shapefile layer.

        Args:
            (shapefile layer) layer: A shapefile layer.
            (shapefile layer) location: A shapefile layer.

        Returns:
            (shapefile layer) layer: A shapefile layer.
        """
        for fld in ZB_C_FIELDS:
            dummy = ogr.FieldDefn(fld, ogr.OFTString)
            dummy.SetWidth(255)
            layer.CreateField(dummy)

        herstelmaatregel = ogr.FieldDefn("Herstelmaa", ogr.OFTString)
        herstelmaatregel.SetWidth(255)
        layer.CreateField(herstelmaatregel)

        opmerking = ogr.FieldDefn("Opmerking", ogr.OFTString)
        opmerking.SetWidth(255)
        layer.CreateField(opmerking)

        artrigger = ogr.FieldDefn("Trigger", ogr.OFTString)
        artrigger.SetWidth(32)
        layer.CreateField(artrigger)
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
        x = manhole["x"]
        y = manhole["y"]
        wkt = "POINT({} {})".format(x, y)

        feature = ogr.Feature(layer.GetLayerDefn())
        point = ogr.CreateGeometryFromWkt(wkt)

        feature.SetGeometry(point)

        for fld in ZB_C_FIELDS:
            feature.SetField(fld, str(manhole.get(fld, ' ')))

        feature.SetField("Herstelmaa", str(manhole.get('Herstelmaatregel', '')))
        feature.SetField("Opmerking", str(manhole.get("Opmerking", '')))
        feature.SetField('Trigger', str(manhole.get('Trigger', '')))

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

        for fld in ZB_A_FIELDS:
            dummy = ogr.FieldDefn(fld, ogr.OFTString)
            dummy.SetWidth(255)
            layer.CreateField(dummy)

        herstelmaatregel = ogr.FieldDefn("Herstelmaa", ogr.OFTString)
        herstelmaatregel.SetWidth(255)
        layer.CreateField(herstelmaatregel)

        opmerking = ogr.FieldDefn("Opmerking", ogr.OFTString)
        opmerking.SetWidth(255)
        layer.CreateField(opmerking)

        artrigger = ogr.FieldDefn("Trigger", ogr.OFTString)
        artrigger.SetWidth(255)
        layer.CreateField(artrigger)

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
        start_x = pipe.get("Beginpunt x", ' ')
        start_y = pipe.get("Beginpunt y", ' ')
        end_x = pipe.get("Eindpunt x", ' ')
        end_y = pipe.get("Eindpunt y", ' ')
        AAA = pipe.get("AAA", ' ')
        AAB = pipe.get("AAB", ' ')
        AAD = pipe.get("AAD", ' ')
        AAE = ", ".join(pipe["AAE"])
        AAF = pipe.get("AAF", ' ')
        AAG = ", ".join(pipe["AAG"])
        AAJ = pipe.get("AAJ", ' ')
        AAK = pipe.get("AAK", ' ')
        AAL = pipe.get("AAL", ' ')
        AAM = pipe.get("AAM", ' ')
        AAN = pipe.get("AAN", ' ')
        AAO = pipe.get("AAO", ' ')
        AAP = pipe.get("AAP", ' ')
        AAQ = pipe.get("AAQ", ' ')
        ABA = pipe.get("ABA", ' ')
        ABB = pipe.get("ABB", ' ')
        ABC = pipe.get("ABC", ' ')
        ABE = pipe.get("ABE", ' ')
        ABF = pipe.get("ABF", ' ')
        ABH = pipe.get("ABH", ' ')
        ABI = pipe.get("ABI", ' ')
        ABJ = pipe.get("ABJ", ' ')
        ABK = pipe.get("ABK", ' ')
        ABL = pipe.get("ABL", ' ')
        ABM = pipe.get("ABM", ' ')
        ABP = pipe.get("ABP", ' ')
        ABQ = pipe.get("ABQ", ' ')
        ABS = pipe.get("ABS", ' ')
        ACA = pipe.get("ACA", ' ')
        ACB = pipe.get("ACB", ' ')
        ACC = pipe.get("ACC", ' ')
        ACD = pipe.get("ACD", ' ')
        ACG = pipe.get("ACG", ' ')
        ACJ = pipe.get("ACJ", ' ')
        ACK = pipe.get("ACK", ' ')
        ACM = pipe.get("ACM", ' ')
        ACN = pipe.get("ACN", ' ')
        ADA = pipe.get("ADA", ' ')
        ADB = pipe.get("ADB", ' ')
        ADC = pipe.get("ADC", ' ')
        AXA = pipe.get("AXA", ' ')
        AXB = pipe.get("AXB", ' ')
        AXF = pipe.get("AXF", ' ')
        AXG = pipe.get("AXG", ' ')
        AXH = pipe.get("AXH", ' ')
        herstelmaatregel = pipe["Herstelmaatregel"]
        # herstelmaatregel = HERSTELMAATREGEL_DEFAULT
        opmerking = pipe["Opmerking"]
        artrigger = pipe.get("Trigger", '')
        ZC = pipe["ZC"]

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
        feature.SetField("Herstelmaa", str(herstelmaatregel))
        feature.SetField("Opmerking", str(opmerking))
        feature.SetField('Trigger', str(artrigger))

        feature.SetField("ZC", str(ZC))
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

        for fld in 'xyABCDEFGIJKMNO':
            dummy = ogr.FieldDefn(fld, ogr.OFTString)
            dummy.SetWidth(255)
            layer.CreateField(dummy)

        herstelmaatregel = ogr.FieldDefn("Herstelmaa", ogr.OFTString)
        herstelmaatregel.SetWidth(255)
        layer.CreateField(herstelmaatregel)

        opmerking = ogr.FieldDefn("Opmerking", ogr.OFTString)
        opmerking.SetWidth(255)
        layer.CreateField(opmerking)
        artrigger = ogr.FieldDefn("Trigger", ogr.OFTString)
        artrigger.SetWidth(32)
        layer.CreateField(artrigger)
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
        x = float(measuring_point["x"]) if measuring_point["x"] else 0.0
        y = float(measuring_point["y"]) if measuring_point["y"] else 0.0
        herstelmaatregel = measuring_point.get("Herstelmaatregel", '')
        opmerking = measuring_point["Opmerking"] if measuring_point["Opmerking"] else ""
        trigger = measuring_point.get('Trigger', '')
        # artrigger = measuring_point['Trigger']

        # Set values
        feature = ogr.Feature(layer.GetLayerDefn())
        wkt = "POINT({} {})".format(x, y)
        point = ogr.CreateGeometryFromWkt(wkt)
        feature.SetGeometry(point)
        feature.SetField("PIPE_ID", str(pipe_id))
        feature.SetField("x", str(x))
        feature.SetField("y", str(y))

        for fld in list('ABCDEFGIJKMNO'):
            feature.SetField(fld, str(measuring_point.get(fld, None)))

        feature.SetField('Herstelmaa', herstelmaatregel)
        feature.SetField('Opmerking', opmerking)
        feature.SetField('Trigger', trigger)

        layer.CreateFeature(feature)

        feature = None
        return layer

def show_shapefile_layers(directory):
    """
    Show the manholes, pipes and measuring points layer.
    Set the manholes layer as active layer to be the same layer as the active
    tab.

    Arguments:
        (string) directory: Directory where the shapefiles are.
            These shapefiles are shown as layers.
    """
    # Manholes
    manholes_filename = "{}.shp".format(SHP_NAME_MANHOLES)
    manholes_path = os.path.join(directory, manholes_filename)
    manholes_layer = iface.addVectorLayer(manholes_path, SHP_NAME_MANHOLES, "ogr")
    # Pipes
    pipes_filename = "{}.shp".format(SHP_NAME_PIPES)
    pipes_path = os.path.join(directory, pipes_filename)
    pipes_layer = iface.addVectorLayer(pipes_path, SHP_NAME_PIPES, "ogr")
    # Measuring stations
    measuring_points_filename = "{}.shp".format(SHP_NAME_MEASURING_POINTS)
    measuring_points_path = os.path.join(directory, measuring_points_filename)
    measuring_points_layer = iface.addVectorLayer(measuring_points_path, SHP_NAME_MEASURING_POINTS, "ogr")
    # Set manholes layer as active layer
    iface.setActiveLayer(manholes_layer)
