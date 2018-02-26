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

from qgis.utils import iface


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