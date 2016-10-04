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

from qgis.core import QgsVectorFileWriter, QgsMapLayerRegistry, QgsGeometry, QgsFeature, QgsPoint

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
        self.setup_radios()
        self.setup_line_edit()
        self.setup_close()
        self.start_point = QgsPoint(0.000, 0.000)

    def setup_line_edit(self):
        self.coord_label.returnPressed.connect(lambda:self.setup_start_point(self.coord_label.text()))
        self.coord_label.editingFinished.connect(self.coord_label.returnPressed)

    def setup_close(self):
        close_button = [b for b in self.button_box.buttons() if b.text() == "Close"][0]
        close_button.clicked.connect(self.close)

    def setup_radios(self):
        self.radio_map.toggled.connect(lambda:self.radio_check(self.radio_map))
        self.radio_text.toggled.connect(lambda:self.radio_check(self.radio_text))

    def set_iface(self, iface):
        self.iface = iface

    def set_dist_limit(self):
        self.dist_limit.textChanged.connect(self.text_changed)
        self.dist_lim_text = self.dist_limit.displayText()

    def text_changed(self, text):
        self.dist_lim_text = text

    def layers_tool(self, layers):
        layer_list = list(map(lambda l: l.name(), layers))
        self.comboBox.addItems(layer_list)
        self.layers = layers

    def set_point_layer(self, start_layer):
        self.start_layer = start_layer

    def set_vl3_layer(self, vl3):
        self.vl3 = vl3

    def radio_check(self, r):
        behave = {"Choose from map": self.activate_tool,
                  "Edit in textbox": self.deactivate_tool}
        behave[r.text()]()

    def activate_tool(self):
        self.coord_label.setReadOnly(True)
        self.point_tool(self.canvas)

    def deactivate_tool(self):
        self.coord_label.setReadOnly(False)
        self.canvas.mapTool() # Reset map tool
        self.iface.actionPan().trigger() # Set to pan tool

    def setup_start_point(self, str_point):
        x, y = eval(str_point)
        start_point = QgsPoint(x, y)
        self.point = start_point
        start_vl = self.start_layer
        startPt = QgsGeometry.fromPoint(start_point) # Get geometry of start point
        startF = QgsFeature() # Create a new feature for the start point
        startF.setGeometry(startPt)
        pr_start = start_vl.dataProvider() # Add start point feature to layer
        start_vl.startEditing()
        pr_start.addFeatures([startF])
        start_vl.updateExtents()
        self.canvas.refresh()
        self.coord_label.setModified(False)

    def point_tool(self, canvas):
        self.canvas = canvas
        self.tool = PointTool(canvas)
        # self.tool.set_win(mainWin)
        self.tool.set_label(self.coord_label)
        self.tool.set_start_layer(self.start_layer)
        self.tool.activate()

    def save_dg(self, caption, type_="shp"):
        types = {"shp": "SHP files (*.shp)",
                 "tif": "TIF files (*.tif)",
                 "all": "All Files (*.*)"}
        filename = QtGui.QFileDialog.getSaveFileName(self, caption, "", types[type_])
        return filename

    # def ask_save(self, start_layer, vl3):
    #     # self.start_layer.commitChanges()
    #     # self.vl3.commitChanges()
    #     start_filename = self.save_dg("Save start point layer as...", type_="shp")
    #     sprov = start_layer.dataProvider()
    #     sfields = sprov.fields()
    #     swriter = QgsVectorFileWriter(start_filename, "CP1250", sfields, sprov.geometryType(), sprov.crs(), "ESRI Shapefile")
    #     sfeat = QgsFeature()
    #     sfeat.setGeometry(start_layer.geometry())
    #     swriter.addFeature(sfeat)
    #     del swriter
    #     area_filename = self.save_dg("Save area of availability layer as...", type_="shp")
    #     aprov = vl3.dataProvider()
    #     afields = aprov.fields()
    #     awriter = QgsVectorFileWriter(area_filename, "CP1250", afields, aprov.geometryType(), aprov.crs(), "ESRI Shapefile")
    #     afeat = QgsFeature()
    #     afeat.setGeometry(vl3.geometry())
    #     awriter.addFeature(afeat)
    #     del awriter

    def closeEvent(self, event):
        self.deactivate_tool()
        feat_ids = self.start_layer.allFeatureIds()
        if len(feat_ids) < 1:
            QgsMapLayerRegistry.instance().removeMapLayers([self.start_layer.id()])
