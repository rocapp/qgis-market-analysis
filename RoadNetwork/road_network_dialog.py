# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RoadNetworkDialog
                                 A QGIS plugin
 Easy-to-use road network and demographics analysis
                             -------------------
        begin                : 2016-08-18
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Robert Capps
        email                : rocapp@gmail.com
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

from PyQt4 import QtGui, uic, QtCore
from point_tool import PointTool

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'road_network_dialog_base.ui'))

class RoadNetworkDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(RoadNetworkDialog, self).__init__(parent)
        QtGui.QDialog.__init__(self, None, QtCore.Qt.WindowStaysOnTopHint)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

    def set_dist_limit(self):
        self.dist_limit.textChanged.connect(self.text_changed)

    def text_changed(self, text):
        self.dist_lim_text = text

    def layers_tool(self, layers):
        layer_list = list(map(lambda l: l.name(), layers))
        self.comboBox.addItems(layer_list)
        self.layers = layers

    def point_tool(self, canvas):
        self.tool = PointTool(canvas)
        self.tool.set_label(self.coord_label)
        canvas.setMapTool(self.tool)
