# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Beoordelingstool
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
import osgeo.ogr as ogr
import osgeo.osr as osr
import os.path
import json
import re

from PyQt4.QtCore import QCoreApplication
from PyQt4.QtCore import QSettings
from PyQt4.QtCore import Qt
from PyQt4.QtCore import QTranslator
from PyQt4.QtCore import qVersion
from PyQt4.QtGui import QAction
from PyQt4.QtGui import QFileDialog
from PyQt4.QtGui import QTableWidgetItem
from PyQt4.QtGui import QIcon
from qgis.core import QgsExpression
from qgis.core import QgsFeature
from qgis.core import QgsFeatureRequest
from qgis.core import QgsMapLayerRegistry
from qgis.utils import iface
# Initialize Qt resources from file resources.py
import resources


# Import the code for the DockWidget
from beoordelingstool_dockwidget import BeoordelingstoolDockWidget

BUTTON_DOWNLOAD_RIOOL = "download_riool_search"
TEXTBOX_DOWNLOAD_RIOOL = "download_riool_text"
# from .utils.constants import BUTTON_DOWNLOAD_PUTTEN
# from .utils.constants import TEXTBOX_DOWNLOAD_PUTTEN
FILE_TYPE_JSON = "json"
# HERSTELMAATREGEL_DEFAULT = 1
# from .utils.constants import FILE_TYPE_JSON
# from .utils.get_data import get_file


class Beoordelingstool:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Beoordelingstool_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Beoordelingstool')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'Beoordelingstool')
        self.toolbar.setObjectName(u'Beoordelingstool')

        #print "** INITIALIZING Beoordelingstool"

        self.pluginIsActive = False
        self.dockwidget = None


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Beoordelingstool', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/Beoordelingstool/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Beoordelingstool'),
            callback=self.run,
            parent=self.iface.mainWindow())

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING Beoordelingstool"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        #print "** UNLOAD Beoordelingstool"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Beoordelingstool'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING Beoordelingstool"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = BeoordelingstoolDockWidget()
                # DOWNLOAD
                # Connect the search buttons with the search_file functions
                # General tab
                self.dockwidget.download_riool_search.clicked.connect(
                    self.search_json_riool)
                self.dockwidget.save_shapefile_putten_button.clicked.connect(
                    self.save_shapefile_putten)
                self.dockwidget.save_shapefile_leidingen_button.clicked.connect(
                    self.save_shapefile_leidingen)
                # Manholes tab
                self.selected_manhole_id = 0
                self.dockwidget.pushbutton_get_selected_manhole.clicked.connect(
                    self.get_selected_manhole)
                self.dockwidget.pushbutton_save_attribute_manholes.clicked.connect(
                    self.save_beoordeling_putten)
                # Pipes tab
                self.selected_pipe_id = 0
                self.dockwidget.pushbutton_get_selected_pipe.clicked.connect(
                    self.get_selected_pipe)
                self.dockwidget.pushbutton_save_attribute_pipes.clicked.connect(
                    self.save_beoordeling_leidingen)
                self.dockwidget.pushbutton_pipe_to_measuring_station.clicked.connect(
                    self.show_measuring_station)
                # Measuring stations tab
                self.selected_measuring_station_id = 0
                self.dockwidget.pushbutton_get_selected_measuring_station.clicked.connect(
                    self.get_selected_measuring_station)
                self.dockwidget.pushbutton_save_attribute_measuring_stations.clicked.connect(
                    self.save_beoordeling_measuring_stations)
                self.dockwidget.pushbutton_measuring_stations_previous.clicked.connect(
                    self.show_previous_measuring_station)
                self.dockwidget.pushbutton_measuring_station_to_pipe.clicked.connect(
                    self.show_pipe)
                self.dockwidget.pushbutton_measuring_stations_next.clicked.connect(
                    self.show_next_measuring_station)

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

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
                self.dockwidget.download_riool_text.setText(filename)
                # print filename  # riool.json

    def save_shapefile_putten(self):
        """
        Function to save the manholes of the json.
        This function also shows the shapefile on the map.
        """

        # Get shapefile path
        save_message = "Save manholes shapefile"
        output = self.get_shapefile_path(save_message)
        shapefile_path = "{}.shp".format(output)
        # Get json
        filename_json = self.dockwidget.download_riool_text.text()
        manholes, pipes = self.get_json(filename_json)

        # Create manhole shapefile
        driver = ogr.GetDriverByName("ESRI Shapefile")
        data_source = driver.CreateDataSource(shapefile_path)
        srs = osr.SpatialReference()
        # manholes[0]["CRS"]  # "Netherlands-RD"
        srs.ImportFromEPSG(28992)  # 4326  4289 RIBx 3857 GoogleMaps
        layer = data_source.CreateLayer(shapefile_path, srs, ogr.wkbPoint)
        layer = self.fields_to_manholes_shp(layer, manholes)
        for manhole in manholes:
            layer = self.feature_to_manholes_shp(layer, manhole)
        data_source = None
        layer = iface.addVectorLayer(shapefile_path, "manholes", "ogr")

    def save_shapefile_leidingen(self):
        """
        Function to save the pipes of the json.
        This function also shows this shapefile on the map.
        """

        # Get shapefile path
        save_message = "Save pipes shapefile"
        output = self.get_shapefile_path(save_message)
        shapefile_path = "{}.shp".format(output)
        # Get json
        filename_json = self.dockwidget.download_riool_text.text()
        manholes, pipes = self.get_json(filename_json)

        # Create pipes shapefile
        driver = ogr.GetDriverByName("ESRI Shapefile")
        data_source = driver.CreateDataSource(shapefile_path)
        srs = osr.SpatialReference()
        # pipes[0]["Beginpunt CRS"]  # "Netherlands-RD"
        srs.ImportFromEPSG(28992)  # 4326  4289 RIBx 3857 GoogleMaps
        layer = data_source.CreateLayer(shapefile_path, srs, ogr.wkbLineString)
        # data_source = None

        # Create measuring points shapefile
        measuring_points_path = os.path.join(os.path.dirname(shapefile_path), "measuring_points.shp")
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
        layer = iface.addVectorLayer(shapefile_path, "pipes", "ogr")
        data_source_measuring_point = None
        measuring_points_layer = iface.addVectorLayer(measuring_points_path, "measuring_points", "ogr")
        # Populate measuring points shapefile

    def get_shapefile_path(self, save_message):
        """Function to get a file."""
        settings = QSettings('beoordelingstool', 'qgisplugin')

        try:
            init_path = settings.value('last_used_import_path', type=str)
        except TypeError:
            init_path = os.path.expanduser("~")
        filename = QFileDialog.getSaveFileName(None,
                                               save_message,
                                               init_path,
                                               'ESRI shapefile (*.shp)')

        if filename:
            settings.setValue('last_used_import_path',
                              os.path.dirname(filename))

        return filename

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

    def get_selected_manhole(self):
        layer = iface.activeLayer()
        fields = layer.dataProvider().fields()
        for f in layer.selectedFeatures():
            self.dockwidget.value_plaintextedit_manholes.setPlainText(str(f["Opmerking"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 0, QTableWidgetItem(f["CAA"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 1, QTableWidgetItem(f["CAJ"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 2, QTableWidgetItem(f["CAL"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 3, QTableWidgetItem(f["CAM"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 4, QTableWidgetItem(f["CAN"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 5, QTableWidgetItem(f["CAO"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 6, QTableWidgetItem(f["CAQ"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 7, QTableWidgetItem(f["CAR"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 8, QTableWidgetItem(f["CBA"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 9, QTableWidgetItem(f["CBB"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 10, QTableWidgetItem(f["CBC"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 11, QTableWidgetItem(f["CBD"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 12, QTableWidgetItem(f["CBE"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 13, QTableWidgetItem(f["CBF"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 14, QTableWidgetItem(f["CBH"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 15, QTableWidgetItem(f["CBI"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 16, QTableWidgetItem(f["CBJ"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 17, QTableWidgetItem(f["CBK"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 18, QTableWidgetItem(f["CBL"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 19, QTableWidgetItem(f["CBM"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 20, QTableWidgetItem(f["CBO"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 21, QTableWidgetItem(f["CBP"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 22, QTableWidgetItem(f["CCA"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 23, QTableWidgetItem(f["CCB"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 24, QTableWidgetItem(f["CCC"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 25, QTableWidgetItem(f["CCD"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 26, QTableWidgetItem(f["CCK"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 27, QTableWidgetItem(f["CCM"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 28, QTableWidgetItem(f["CCN"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 29, QTableWidgetItem(f["CCO"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 30, QTableWidgetItem(f["CCP"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 31, QTableWidgetItem(f["CCQ"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 32, QTableWidgetItem(f["CCR"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 33, QTableWidgetItem(f["CCS"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 34, QTableWidgetItem(f["CDA"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 35, QTableWidgetItem(f["CDB"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 36, QTableWidgetItem(f["CDC"]))
            self.dockwidget.tablewidget_manholes.setItem(0, 37, QTableWidgetItem(f["CDD"]))
            self.selected_manhole_id = f.id()

    def save_beoordeling_putten(self):
        """Save herstelmaatregel and opmerking in the shapefile."""
        layer = iface.activeLayer()
        fid = self.selected_manhole_id
        herstelmaatregel = str(self.dockwidget.field_combobox_manholes.currentText())
        opmerking = str(self.dockwidget.value_plaintextedit_manholes.toPlainText())
        layer.startEditing()
        layer.changeAttributeValue(fid, 38, herstelmaatregel)  # Herstelmaatregel
        layer.changeAttributeValue(fid, 39, opmerking)  # Opmerking
        layer.commitChanges()
        layer.triggerRepaint()

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

    def get_selected_pipe(self):
        layer = iface.activeLayer()
        fields = layer.dataProvider().fields()
        for f in layer.selectedFeatures():
            self.dockwidget.value_plaintextedit_pipes.setPlainText(str(f["Opmerking"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 0, QTableWidgetItem(f["AAA"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 1, QTableWidgetItem(f["AAB"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 2, QTableWidgetItem(f["AAD"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 3, QTableWidgetItem(f["AAE"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 4, QTableWidgetItem(f["AAF"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 5, QTableWidgetItem(f["AAG"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 6, QTableWidgetItem(f["AAJ"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 7, QTableWidgetItem(f["AAK"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 8, QTableWidgetItem(f["AAL"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 9, QTableWidgetItem(f["AAM"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 10, QTableWidgetItem(f["AAN"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 11, QTableWidgetItem(f["AAO"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 12, QTableWidgetItem(f["AAP"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 13, QTableWidgetItem(f["AAQ"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 14, QTableWidgetItem(f["ABA"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 15, QTableWidgetItem(f["ABB"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 16, QTableWidgetItem(f["ABC"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 17, QTableWidgetItem(f["ABE"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 18, QTableWidgetItem(f["ABF"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 19, QTableWidgetItem(f["ABH"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 20, QTableWidgetItem(f["ABI"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 21, QTableWidgetItem(f["ABJ"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 22, QTableWidgetItem(f["ABK"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 23, QTableWidgetItem(f["ABL"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 24, QTableWidgetItem(f["ABM"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 25, QTableWidgetItem(f["ABP"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 26, QTableWidgetItem(f["ABQ"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 27, QTableWidgetItem(f["ABS"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 28, QTableWidgetItem(f["ACA"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 29, QTableWidgetItem(f["ACB"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 30, QTableWidgetItem(f["ACC"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 31, QTableWidgetItem(f["ACD"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 32, QTableWidgetItem(f["ACG"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 33, QTableWidgetItem(f["ACJ"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 34, QTableWidgetItem(f["ACK"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 35, QTableWidgetItem(f["ACM"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 36, QTableWidgetItem(f["ACN"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 37, QTableWidgetItem(f["ADA"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 38, QTableWidgetItem(f["ADB"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 39, QTableWidgetItem(f["ADC"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 40, QTableWidgetItem(f["AXA"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 41, QTableWidgetItem(f["AXB"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 42, QTableWidgetItem(f["AXF"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 43, QTableWidgetItem(f["AXG"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 44, QTableWidgetItem(f["AXH"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 45, QTableWidgetItem(f["ZC"]))
            self.selected_pipe_id = f.id()

    def save_beoordeling_leidingen(self):
        """Save herstelmaatregel and opmerking in the shapefile."""
        layer = iface.activeLayer()
        fid = self.selected_pipe_id
        herstelmaatregel = str(self.dockwidget.field_combobox_pipes.currentText())
        opmerking = str(self.dockwidget.value_plaintextedit_pipes.toPlainText())
        layer.startEditing()
        layer.changeAttributeValue(fid, 47, herstelmaatregel)  # Herstelmaatregel
        layer.changeAttributeValue(fid, 48, opmerking)  # Opmerking
        layer.commitChanges()
        layer.triggerRepaint()

    def show_measuring_station(self):
        """Show the measuring station that belongs to a certain pipe."""
        try:
            current_measuring_point_pipe_id = self.dockwidget.tablewidget_measuring_stations.itemAt(0,0).text()
        except:  # No measuring point selected
            current_measuring_point_pipe_id = -1
        if current_measuring_point_pipe_id != self.selected_pipe_id:
            # Get first measuring point of pipe
            layerList = QgsMapLayerRegistry.instance().mapLayersByName("measuring_points")
            if layerList:
                layer = layerList[0]
                expr = QgsExpression("\"PIPE_ID\" IS '{}'".format(self.selected_pipe_id))
                measuring_points = layer.getFeatures(QgsFeatureRequest(expr))  #.next()
                ids = [measuring_point.id() for measuring_point in measuring_points]  # select only the features for which the expression is true
                print ids
                first_id = ids[0]
                last_id = ids[-1] if ids[-1] else ids[0]
                self.selected_measuring_station_id = first_id
                print self.selected_measuring_station_id
                layer.setSelectedFeatures([int(self.selected_measuring_station_id)])
                new_feature = layer.selectedFeatures()[0]
                # measuring_station_id = 1
                # self.selected_measuring_station_id = measuring_station_id
                # print self.selected_measuring_station_id
                # layerList = QgsMapLayerRegistry.instance().mapLayersByName("measuring_points")
                # if layerList:
                #     layer = layerList[0]
                #     layer.setSelectedFeatures([int(self.selected_measuring_station_id)])
                #     new_feature = layer.selectedFeatures()[0]

                # Set values
                self.dockwidget.value_plaintextedit_measuring_stations.setPlainText(new_feature["Opmerking"] if new_feature["Opmerking"] else '')
                self.dockwidget.tablewidget_measuring_stations.setItem(0, 0, QTableWidgetItem(new_feature["PIPE_ID"]))
                self.dockwidget.tablewidget_measuring_stations.setItem(0, 1, QTableWidgetItem(new_feature["A"]))
                self.dockwidget.tablewidget_measuring_stations.setItem(0, 2, QTableWidgetItem(new_feature["B"]))
                self.dockwidget.tablewidget_measuring_stations.setItem(0, 3, QTableWidgetItem(new_feature["C"]))
                self.dockwidget.tablewidget_measuring_stations.setItem(0, 4, QTableWidgetItem(new_feature["D"]))
                self.dockwidget.tablewidget_measuring_stations.setItem(0, 5, QTableWidgetItem(new_feature["E"]))
                self.dockwidget.tablewidget_measuring_stations.setItem(0, 6, QTableWidgetItem(new_feature["F"]))
                self.dockwidget.tablewidget_measuring_stations.setItem(0, 7, QTableWidgetItem(new_feature["G"]))
                self.dockwidget.tablewidget_measuring_stations.setItem(0, 8, QTableWidgetItem(new_feature["I"]))
                self.dockwidget.tablewidget_measuring_stations.setItem(0, 9, QTableWidgetItem(new_feature["J"]))
                self.dockwidget.tablewidget_measuring_stations.setItem(0, 10, QTableWidgetItem(new_feature["K"] if new_feature["K"] else None))
                self.dockwidget.tablewidget_measuring_stations.setItem(0, 11, QTableWidgetItem(new_feature["M"]))
                self.dockwidget.tablewidget_measuring_stations.setItem(0, 12, QTableWidgetItem(new_feature["N"]))
                self.dockwidget.tablewidget_measuring_stations.setItem(0, 13, QTableWidgetItem(new_feature["O"]))
                iface.setActiveLayer(layer)

        layer.triggerRepaint()
        # Go to measuring stations tab
        self.dockwidget.tabWidget.setCurrentIndex(3)

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

    def get_selected_measuring_station(self):
        layer = iface.activeLayer()
        fields = layer.dataProvider().fields()
        for f in layer.selectedFeatures():
            self.dockwidget.value_plaintextedit_measuring_stations.setPlainText(str(f["Opmerking"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 0, QTableWidgetItem(f["PIPE_ID"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 1, QTableWidgetItem(f["A"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 2, QTableWidgetItem(f["B"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 3, QTableWidgetItem(f["C"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 4, QTableWidgetItem(f["D"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 5, QTableWidgetItem(f["E"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 6, QTableWidgetItem(f["F"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 7, QTableWidgetItem(f["G"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 8, QTableWidgetItem(f["I"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 9, QTableWidgetItem(f["J"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 10, QTableWidgetItem(f["K"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 11, QTableWidgetItem(f["M"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 12, QTableWidgetItem(f["N"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 13, QTableWidgetItem(f["O"]))
            self.selected_measuring_station_id = f.id()

    def show_previous_measuring_station(self):
        """Show the next measuring station."""
        # Show message if first id and clicked on again (can't go back further)
        # Only show if still same pipe
        layer = iface.activeLayer()
        features_amount = layer.featureCount()
        measuring_station_id_new = self.selected_measuring_station_id - 1
        if measuring_station_id_new > -1:
            self.selected_measuring_station_id = measuring_station_id_new
            layer.setSelectedFeatures([int(self.selected_measuring_station_id)])
            new_feature = layer.selectedFeatures()[0]

            # Set values
            self.dockwidget.value_plaintextedit_measuring_stations.setPlainText(new_feature["Opmerking"] if new_feature["Opmerking"] else '')
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 0, QTableWidgetItem(new_feature["PIPE_ID"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 1, QTableWidgetItem(new_feature["A"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 2, QTableWidgetItem(new_feature["B"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 3, QTableWidgetItem(new_feature["C"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 4, QTableWidgetItem(new_feature["D"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 5, QTableWidgetItem(new_feature["E"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 6, QTableWidgetItem(new_feature["F"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 7, QTableWidgetItem(new_feature["G"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 8, QTableWidgetItem(new_feature["I"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 9, QTableWidgetItem(new_feature["J"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 10, QTableWidgetItem(new_feature["K"] if new_feature["K"] else None))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 11, QTableWidgetItem(new_feature["M"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 12, QTableWidgetItem(new_feature["N"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 13, QTableWidgetItem(new_feature["O"]))
        layer.triggerRepaint()

    def show_pipe(self):
        """Show the pipe to which a measuring station belongs."""
        pipe_id = self.dockwidget.tablewidget_measuring_stations.itemAt(0,0).text() if self.dockwidget.tablewidget_measuring_stations.itemAt(0,0) else 1
        self.selected_pipe_id = pipe_id
        print pipe_id
        layerList = QgsMapLayerRegistry.instance().mapLayersByName("pipes")
        if layerList:
            layer = layerList[0]
            layer.setSelectedFeatures([int(self.selected_pipe_id)])
            new_feature = layer.selectedFeatures()[0]
            self.dockwidget.value_plaintextedit_pipes.setPlainText(str(new_feature["Opmerking"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 0, QTableWidgetItem(new_feature["AAA"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 1, QTableWidgetItem(new_feature["AAB"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 2, QTableWidgetItem(new_feature["AAD"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 3, QTableWidgetItem(new_feature["AAE"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 4, QTableWidgetItem(new_feature["AAF"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 5, QTableWidgetItem(new_feature["AAG"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 6, QTableWidgetItem(new_feature["AAJ"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 7, QTableWidgetItem(new_feature["AAK"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 8, QTableWidgetItem(new_feature["AAL"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 9, QTableWidgetItem(new_feature["AAM"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 10, QTableWidgetItem(new_feature["AAN"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 11, QTableWidgetItem(new_feature["AAO"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 12, QTableWidgetItem(new_feature["AAP"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 13, QTableWidgetItem(new_feature["AAQ"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 14, QTableWidgetItem(new_feature["ABA"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 15, QTableWidgetItem(new_feature["ABB"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 16, QTableWidgetItem(new_feature["ABC"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 17, QTableWidgetItem(new_feature["ABE"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 18, QTableWidgetItem(new_feature["ABF"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 19, QTableWidgetItem(new_feature["ABH"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 20, QTableWidgetItem(new_feature["ABI"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 21, QTableWidgetItem(new_feature["ABJ"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 22, QTableWidgetItem(new_feature["ABK"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 23, QTableWidgetItem(new_feature["ABL"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 24, QTableWidgetItem(new_feature["ABM"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 25, QTableWidgetItem(new_feature["ABP"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 26, QTableWidgetItem(new_feature["ABQ"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 27, QTableWidgetItem(new_feature["ABS"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 28, QTableWidgetItem(new_feature["ACA"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 29, QTableWidgetItem(new_feature["ACB"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 30, QTableWidgetItem(new_feature["ACC"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 31, QTableWidgetItem(new_feature["ACD"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 32, QTableWidgetItem(new_feature["ACG"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 33, QTableWidgetItem(new_feature["ACJ"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 34, QTableWidgetItem(new_feature["ACK"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 35, QTableWidgetItem(new_feature["ACM"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 36, QTableWidgetItem(new_feature["ACN"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 37, QTableWidgetItem(new_feature["ADA"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 38, QTableWidgetItem(new_feature["ADB"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 39, QTableWidgetItem(new_feature["ADC"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 40, QTableWidgetItem(new_feature["AXA"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 41, QTableWidgetItem(new_feature["AXB"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 42, QTableWidgetItem(new_feature["AXF"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 43, QTableWidgetItem(new_feature["AXG"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 44, QTableWidgetItem(new_feature["AXH"]))
            self.dockwidget.tablewidget_pipes.setItem(0, 45, QTableWidgetItem(new_feature["ZC"]))
            iface.setActiveLayer(layer)
            layer.triggerRepaint()
            # Go to the pipe tab
            self.dockwidget.tabWidget.setCurrentIndex(2)

    def show_next_measuring_station(self):
        """Show the next measuring station."""
        # Only show if still same pipe
        # Show message if first id and clicked on again (can't go further)
        layer = iface.activeLayer()
        features_amount = layer.featureCount()
        measuring_station_id_new = self.selected_measuring_station_id + 1
        if measuring_station_id_new < features_amount:
            self.selected_measuring_station_id = measuring_station_id_new
            layer.setSelectedFeatures([int(self.selected_measuring_station_id)])
            new_feature = layer.selectedFeatures()[0]

            # Set values
            self.dockwidget.value_plaintextedit_measuring_stations.setPlainText(new_feature["Opmerking"] if new_feature["Opmerking"] else '')
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 0, QTableWidgetItem(new_feature["PIPE_ID"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 1, QTableWidgetItem(new_feature["A"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 2, QTableWidgetItem(new_feature["B"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 3, QTableWidgetItem(new_feature["C"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 4, QTableWidgetItem(new_feature["D"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 5, QTableWidgetItem(new_feature["E"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 6, QTableWidgetItem(new_feature["F"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 7, QTableWidgetItem(new_feature["G"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 8, QTableWidgetItem(new_feature["I"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 9, QTableWidgetItem(new_feature["J"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 10, QTableWidgetItem(new_feature["K"] if new_feature["K"] else None))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 11, QTableWidgetItem(new_feature["M"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 12, QTableWidgetItem(new_feature["N"]))
            self.dockwidget.tablewidget_measuring_stations.setItem(0, 13, QTableWidgetItem(new_feature["O"]))
            layer.triggerRepaint()

    def save_beoordeling_measuring_stations(self):
        """Save herstelmaatregel and opmerking in the shapefile."""
        layer = iface.activeLayer()
        fid = self.selected_measuring_station_id
        herstelmaatregel = str(self.dockwidget.field_combobox_measuring_stations.currentText())
        opmerking = str(self.dockwidget.value_plaintextedit_measuring_stations.toPlainText())
        layer.startEditing()
        layer.changeAttributeValue(fid, 16, herstelmaatregel)  # Herstelmaatregel
        layer.changeAttributeValue(fid, 17, opmerking)  # Opmerking
        layer.commitChanges()
        layer.triggerRepaint()
