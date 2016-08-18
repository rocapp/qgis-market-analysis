# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RoadNetwork
                                 A QGIS plugin
 Easy-to-use road network and demographics analysis
                             -------------------
        begin                : 2016-08-18
        copyright            : (C) 2016 by Robert Capps
        email                : rocapp@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load RoadNetwork class from file RoadNetwork.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .road_network import RoadNetwork
    return RoadNetwork(iface)
