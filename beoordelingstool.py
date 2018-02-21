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
import json
import os.path
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
from qgis.gui import QgsMessageBar
from qgis.utils import iface
# Initialize Qt resources from file resources.py
import resources


# Import the code for the DockWidget
from beoordelingstool_dockwidget import BeoordelingstoolDockWidget
from beoordelingstool_download_dialog import BeoordelingstoolDownloadDialog
from beoordelingstool_login_dialog import BeoordelingstoolLoginDialog

# Import constants
from .utils.constants import JSON_NAME
from .utils.constants import JSON_KEY_PROJ
from .utils.constants import JSON_KEY_NAME
from .utils.constants import JSON_KEY_URL
from .utils.constants import JSON_KEY_URL_JSON
from .utils.constants import JSON_KEY_URL_ZIP

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
        self.download_dialog = None


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
        self.dockWidget = None
        self.iface.removeDockWidget(self.dockwidget)


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

        manholes_layerList = QgsMapLayerRegistry.instance().mapLayersByName("manholes")
        pipes_layerList = QgsMapLayerRegistry.instance().mapLayersByName("pipes")
        measuring_stations_layerList = QgsMapLayerRegistry.instance().mapLayersByName("measuring_points")
        if not self.pluginIsActive:

            #print "** STARTING Beoordelingstool"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            # Check if the layers manholes, pipes and measuring_stations are active
            if not manholes_layerList or not pipes_layerList or not measuring_stations_layerList:
                iface.messageBar().pushMessage("Warning", "You don't have a manholes, pipes and measuring_points layer. \n Upload a json.", level=QgsMessageBar.WARNING, duration=0)
                self.download_dialog = BeoordelingstoolDownloadDialog()
                self.download_dialog.show()
            else:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = BeoordelingstoolDockWidget()
                # Create the login dialog for uploading the voortgang
                self.login_dialog_voortgang = BeoordelingstoolLoginDialog()
                self.login_dialog_voortgang.output.connect(self.upload_voortgang)
                # Create the login dialog for uploading the final version
                self.login_dialog_final = BeoordelingstoolLoginDialog()
                self.login_dialog_final.output.connect(self.upload_final)
                # DOWNLOAD
                # General tab
                # Show project name on General tab
                self.set_project_name()
                self.dockwidget.pushbutton_upload_voortgang_json.clicked.connect(
                    self.show_login_dialog_voortgang)
                self. dockwidget.pushbutton_upload_final_json.clicked.connect(
                    self.show_login_dialog_final)
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
                self.pluginIsActive = True
                # Set the active layer to the manholes layer to be in
                # compliance with the Manholes tab of the dockwidget.
                iface.setActiveLayer(manholes_layerList[0])

        # Show a message if not all layers are active
        elif self.pluginIsActive:
            if not manholes_layerList or not pipes_layerList or not measuring_stations_layerList:
                self.iface.removeDockWidget(self.dockwidget)
                self.dockwidget = None
                self.pluginIsActive = False
                iface.messageBar().pushMessage("Warning", "You don't have a manholes, pipes and measuring_points layer. \n Upload a json.", level=QgsMessageBar.WARNING, duration=0)
                self.download_dialog = BeoordelingstoolDownloadDialog()
                self.download_dialog.show()

    def set_project_name(self):
        """
        Set the project name on the General tab of the dockwidget.
        The name of the project_name property of the review.json in the same
        folder as the layer is used as the project name.
        """
        # Check if the manholes, pipes and measuring_points layers exist
        manholes_layerList = QgsMapLayerRegistry.instance().mapLayersByName("manholes")
        pipes_layerList = QgsMapLayerRegistry.instance().mapLayersByName("pipes")
        measuring_stations_layerList = QgsMapLayerRegistry.instance().mapLayersByName("measuring_points")
        if manholes_layerList and pipes_layerList and measuring_stations_layerList:
            # Get project name from the json saved in the same folder as the "manholes" layer
            layer_dir = get_layer_dir(manholes_layerList[0])
            json_path = os.path.join(layer_dir, JSON_NAME)
            try:
                data = json.load(open(json_path))
                if data[JSON_KEY_PROJ][JSON_KEY_NAME]:
                    self.dockwidget.label_project_name.setText(data[JSON_KEY_PROJ][JSON_KEY_NAME])
                else:
                    iface.messageBar().pushMessage("Warning", "No project name defined.", level=QgsMessageBar.WARNING, duration=0)
            except:
                iface.messageBar().pushMessage("Error", "No review.json found.", level=QgsMessageBar.CRITICAL, duration=0)

    def get_selected_manhole(self):
        layer = iface.activeLayer()
        fields = layer.dataProvider().fields()
        for f in layer.selectedFeatures():
            self.dockwidget.field_combobox_manholes.setCurrentIndex(self.dockwidget.field_combobox_manholes.findText(str(f["Herstelmaa"]))) if self.dockwidget.field_combobox_manholes.findText(str(f["Herstelmaa"])) else self.dockwidget.field_combobox_manholes.setCurrentIndex(0)
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

    def get_selected_pipe(self):
        layer = iface.activeLayer()
        fields = layer.dataProvider().fields()
        for f in layer.selectedFeatures():
            self.dockwidget.field_combobox_pipes.setCurrentIndex(self.dockwidget.field_combobox_pipes.findText(str(f["Herstelmaa"]))) if self.dockwidget.field_combobox_pipes.findText(str(f["Herstelmaa"])) else self.dockwidget.field_combobox_pipes.setCurrentIndex(0)
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
        # if current_measuring_point_pipe_id != self.selected_pipe_id:
        layerList = QgsMapLayerRegistry.instance().mapLayersByName("measuring_points")
        if layerList:
            layer = layerList[0]
            expr = QgsExpression("\"PIPE_ID\" IS '{}'".format(self.selected_pipe_id))
            measuring_points = layer.getFeatures(QgsFeatureRequest(expr))  #.next()
            ids = [measuring_point.id() for measuring_point in measuring_points]  # select only the features for which the expression is true
            first_id = ids[0]
            last_id = ids[-1] if ids[-1] else ids[0]
            # Show selected measuring station if it belongs to the selected pipe
            if self.selected_measuring_station_id >= first_id and self.selected_measuring_station_id <= last_id:
                pass
            # Show first measuring station that belongs to the selected pipe:
            else:
                self.selected_measuring_station_id = first_id
            layer.setSelectedFeatures([int(self.selected_measuring_station_id)])
            new_feature = layer.selectedFeatures()[0]

            # Set values
            self.dockwidget.field_combobox_measuring_stations.setCurrentIndex(self.dockwidget.field_combobox_measuring_stations.findText(str(new_feature["Herstelmaa"]))) if self.dockwidget.field_combobox_measuring_stations.findText(str(new_feature["Herstelmaa"])) else self.dockwidget.field_combobox_measuring_stations.setCurrentIndex(0)
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

    def get_selected_measuring_station(self):
        layer = iface.activeLayer()
        fields = layer.dataProvider().fields()
        for f in layer.selectedFeatures():
            self.dockwidget.field_combobox_measuring_stations.setCurrentIndex(self.dockwidget.field_combobox_measuring_stations.findText(str(f["Herstelmaa"]))) if self.dockwidget.field_combobox_measuring_stations.findText(str(f["Herstelmaa"])) else self.dockwidget.field_combobox_measuring_stations.setCurrentIndex(0)
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
        if self.selected_measuring_station_id <= 0:
            iface.messageBar().pushMessage("Info", "This pipe has no previous measuring station.", level=QgsMessageBar.INFO, duration=0)
            return
        current_measuring_station_id = self.selected_measuring_station_id
        current_pipe_id = self.selected_pipe_id

        layer = iface.activeLayer()
        features_amount = layer.featureCount()
        measuring_station_id_new = self.selected_measuring_station_id - 1
        if measuring_station_id_new > -1:
            layer.setSelectedFeatures([int(measuring_station_id_new)])
            new_feature = layer.selectedFeatures()[0]
            pipe_id_new = int(new_feature["PIPE_ID"])
            # Only show the new measuring station if it belongs to the same
            # pipe
            if current_pipe_id == pipe_id_new:
                # Set values
                self.selected_measuring_station_id = measuring_station_id_new
                # Update Measuring stations tab and tablewidget
                self.dockwidget.field_combobox_measuring_stations.setCurrentIndex(self.dockwidget.field_combobox_measuring_stations.findText(str(new_feature["Herstelmaa"]))) if self.dockwidget.field_combobox_measuring_stations.findText(str(new_feature["Herstelmaa"])) else self.dockwidget.field_combobox_measuring_stations.setCurrentIndex(0)
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
            else:
                layer.setSelectedFeatures([int(self.selected_measuring_station_id)])
                iface.messageBar().pushMessage("Info", "This pipe has no previous measuring station.", level=QgsMessageBar.INFO, duration=0)


    def show_pipe(self):
        """Show the pipe to which a measuring station belongs."""
        pipe_id = self.dockwidget.tablewidget_measuring_stations.itemAt(0,0).text() if self.dockwidget.tablewidget_measuring_stations.itemAt(0,0) else 1
        self.selected_pipe_id = pipe_id
        layerList = QgsMapLayerRegistry.instance().mapLayersByName("pipes")
        if layerList:
            layer = layerList[0]
            layer.setSelectedFeatures([int(self.selected_pipe_id)])
            new_feature = layer.selectedFeatures()[0]
            self.dockwidget.field_combobox_pipes.setCurrentIndex(self.dockwidget.field_combobox_pipes.findText(str(new_feature["Herstelmaa"]))) if self.dockwidget.field_combobox_pipes.findText(str(new_feature["Herstelmaa"])) else self.dockwidget.field_combobox_pipes.setCurrentIndex(0)
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
        current_measuring_station_id = self.selected_measuring_station_id
        current_pipe_id = self.selected_pipe_id

        layer = iface.activeLayer()
        features_amount = layer.featureCount()
        measuring_station_id_new = self.selected_measuring_station_id + 1
        if measuring_station_id_new < features_amount:
            layer.setSelectedFeatures([int(self.selected_measuring_station_id) + 1])
            new_feature = layer.selectedFeatures()[0]
            pipe_id_new = int(new_feature["PIPE_ID"])
            # Only show the new measuring station if it belongs to the same
            # pipe
            if current_pipe_id == pipe_id_new:
                # Set values
                self.selected_measuring_station_id = measuring_station_id_new
                # Update Measuring stations tab and tablewidget

                self.dockwidget.field_combobox_measuring_stations.setCurrentIndex(self.dockwidget.field_combobox_measuring_stations.findText(str(new_feature["Herstelmaa"]))) if self.dockwidget.field_combobox_measuring_stations.findText(str(new_feature["Herstelmaa"])) else self.dockwidget.field_combobox_measuring_stations.setCurrentIndex(0)
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
            else:
                layer.setSelectedFeatures([int(self.selected_measuring_station_id)])
                iface.messageBar().pushMessage("Info", "This pipe has no next measuring station.", level=QgsMessageBar.INFO, duration=0)

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

    def show_login_dialog_voortgang(self):
        """
        Show the login dialog.

        If the user data typed in the login dialog is correct, a json
        is created from the shapefiles and uploaded to the server.
        """
        self.login_dialog_voortgang.show()

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
        self.convert_shps_to_json(user_data)
        # upload json to server (get url from json)
        iface.messageBar().pushMessage("Info", "JSON saved.", level=QgsMessageBar.INFO, duration=0)

    def upload_final(self, user_data):
        """Upload the final version (json + zip with shapefiles and qmls)."""
        print "final"
        self.convert_shps_to_json(user_data)
        # save zip
        # upload json and zip to server (get url from json)
        iface.messageBar().pushMessage("Info", "JSON and ZIP? saved.", level=QgsMessageBar.INFO, duration=0)

    def convert_shps_to_json(self, user_data):
        """
        Convert the manholes, pipes and measuring points shapefiles to a json.

        Args:
            (dict) user_data: A dict containing the username and password.
        """
        # Check if the manholes, pipes and measuring_points layers exist
        manholes_layerList = QgsMapLayerRegistry.instance().mapLayersByName("manholes")
        pipes_layerList = QgsMapLayerRegistry.instance().mapLayersByName("pipes")
        measuring_stations_layerList = QgsMapLayerRegistry.instance().mapLayersByName("measuring_points")
        if manholes_layerList and pipes_layerList and measuring_stations_layerList:
            # Check user login credentials ()
            username = user_data["username"]
            password = user_data["password"]
            # Get directory to save json in
            layer_dir = get_layer_dir(manholes_layerList[0])
            json_path = os.path.join(layer_dir, JSON_NAME)
            # Pipes
            pipes = create_pipes_json(pipes_layerList[0], measuring_stations_layerList[0])
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
                    return
                if data[JSON_KEY_PROJ][JSON_KEY_URL]:
                    json_project[JSON_KEY_URL] = data[JSON_KEY_PROJ][JSON_KEY_URL]
                else:
                    iface.messageBar().pushMessage("Error", "No project url found.", level=QgsMessageBar.CRITICAL, duration=0)
                    return
                if data[JSON_KEY_PROJ][JSON_KEY_URL_JSON]:
                    json_project[JSON_KEY_URL_JSON] = data[JSON_KEY_PROJ][JSON_KEY_URL_JSON]
                else:
                    iface.messageBar().pushMessage("Error", "No upload url found for the JSON.", level=QgsMessageBar.CRITICAL, duration=0)
                    return
                if data[JSON_KEY_PROJ][JSON_KEY_URL_ZIP]:
                    json_project[JSON_KEY_URL_ZIP] = data[JSON_KEY_PROJ][JSON_KEY_URL_ZIP]
                else:
                    iface.messageBar().pushMessage("Error", "No upload url found for the zip-file.", level=QgsMessageBar.CRITICAL, duration=0)
                    return
            else:
                iface.messageBar().pushMessage("Error", "No json found.", level=QgsMessageBar.CRITICAL, duration=0)
                return
            json_[JSON_KEY_PROJ] = json_project
            json_["pipes"] = pipes
            json_["manholes"] = manholes
            with open("{}".format(json_path), 'w') as outfile:
                json.dump(json_, outfile, indent=2)
        else:
            iface.messageBar().pushMessage("Warning", "You don't have a manholes, pipes and measuring_points layer.", level=QgsMessageBar.WARNING, duration=0)


def get_layer_dir(layer):
    """
    Function to get the directory of a layer.

    Args:
       (QGIS layer) layer: A layer in QGIS.

    Returns
        (str) directory: The directory in which the layer is saved.
    """
    layer_path = iface.activeLayer().dataProvider().dataSourceUri()
    (directory, shapefile_name) = os.path.split(layer_path)
    return directory

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

def create_pipes_json(pipes_layer, measuring_stations_layer):
    """
    Create a pipes dict from the pipes and measuring stations shapefile.
    One pipe can have 0/> measuring stations.

    Args:
        (shapefile) pipes_shapefile: The pipes shapefile.
        (shapefile) measuring_stations_shapefile: The measuring stations shapefile.

    Returns:
        (dict) pipes: A dict containing the information from the
            pipes and measuring stations shapefile.
    """
    idx = measuring_stations_layer.fieldNameIndex("PIPE_ID")
    values = measuring_stations_layer.uniqueValues(idx)
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
            measuring_stations_layer_specific_pipe = measuring_stations_layer.getFeatures(request)
            pipe["ZC"] = create_measuring_stations_list(measuring_stations_layer_specific_pipe)
        pipes_list.append(pipe)

    return pipes_list

def create_measuring_stations_list(measuring_stations_layer):
    """
    Create a list from the measuring stations shapefile.
    A list item is a json, representing a measuring station.

    Args:
        (shapefile) measuring_stations_shapefile: The measuring stations 
            shapefile.

    Returns:
        (list) measuring_station_list: A list containing the information from
            the measuring stations shapefile. A list item is a measuring
            station, represented by a json.
    """
    measuring_stations_list = []
    for feature in measuring_stations_layer:
        measuring_station = {}
        if feature["A"] and feature["A"] != "None": measuring_station["A"] = str(feature["A"])
        if feature["B"] and feature["B"] != "None": measuring_station["B"] = str(feature["B"])
        if feature["C"] and feature["C"] != "None": measuring_station["C"] = str(feature["C"])
        if feature["D"] and feature["D"] != "None": measuring_station["D"] = str(feature["D"])
        if feature["E"] and feature["E"] != "None": measuring_station["E"] = str(feature["E"])
        if feature["F"] and feature["F"] != "None": measuring_station["F"] = str(feature["F"])
        if feature["G"] and feature["G"] != "None": measuring_station["G"] = str(feature["G"])
        if feature["I"] and feature["I"] != "None": measuring_station["I"] = str(feature["I"])
        if feature["J"] and feature["J"] != "None": measuring_station["J"] = str(feature["J"])
        if feature["K"] and feature["K"] != "None": measuring_station["K"] = str(feature["K"])
        if feature["M"] and feature["M"] != "None": measuring_station["M"] = str(feature["M"])
        if feature["N"] and feature["N"] != "None": measuring_station["N"] = str(feature["N"])
        if feature["O"] and feature["O"] != "None": measuring_station["O"] = str(feature["O"])
        herstelmaatregel = str(feature["Herstelmaa"]) if str(feature["Herstelmaa"]) is not "NULL" else ""
        measuring_station["Herstelmaatregel"] = herstelmaatregel
        opmerking = str(feature["Opmerking"]) if str(feature["Opmerking"]) is not "NULL" else ""
        measuring_station["Opmerking"] = opmerking
        # x & y of measuring points json are saved in the json as tuples  #  x': (146777.899562,)
        measuring_station["y"] = float(feature.geometry().asPoint().y())
        measuring_station["x"] = float(feature.geometry().asPoint().x())
        measuring_stations_list.append(measuring_station)
    return measuring_stations_list
