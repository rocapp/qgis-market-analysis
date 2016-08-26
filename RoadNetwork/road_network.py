# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RoadNetwork
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

from qgis.core import *
from qgis.gui import *
from qgis.networkanalysis import *
import qgis.utils
from qgis.analysis import QgsGeometryAnalyzer

import time

from PyQt4.QtCore import * # QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QProgressBar
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from road_network_dialog import RoadNetworkDialog
import os.path

class RoadNetwork:
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
            'RoadNetwork_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = RoadNetworkDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Rocky Branches - Market Analysis')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'RoadNetwork')
        self.toolbar.setObjectName(u'RoadNetwork')

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
        return QCoreApplication.translate('RoadNetwork', message)


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

        icon_path = ':/plugins/RoadNetwork/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'RB - Market Analysis'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Rocky Branches - Market Analysis'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        layer_set = list()
        layer_set.append(QgsMapCanvasLayer(self.iface.activeLayer()))

        self.dlg.set_dist_limit() # Set up boundary limit text
        start_vl = QgsVectorLayer("Point", "Start Point", "memory") # Layer containing start point
        start_ml = QgsMapCanvasLayer(start_vl)
        layer_set.insert(0, start_ml)
        self.iface.mapCanvas().setLayerSet(layer_set)

        crs_string = "?crs=%s" % (start_vl.crs().toWkt(),) # Get CRS from start point layer
        QgsMapLayerRegistry.instance().addMapLayer(start_vl)
        self.dlg.set_point_layer(start_vl) # Set start point layer
        self.dlg.layers_tool(self.iface.legendInterface().layers())
        self.dlg.point_tool(self.iface.mapCanvas())
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            pMessage = self.iface.messageBar().createMessage("Calculating distances...")
            progress = QProgressBar()
            progress.setMaximum(100)
            progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
            pMessage.layout().addWidget(progress)
            self.iface.messageBar().pushWidget(pMessage, self.iface.messageBar().INFO)

            self.iface.mapCanvas().mapTool() # Reset map tool
            self.iface.actionPan().trigger() # Set to pan tool

            start_point = self.dlg.tool.point # Get selected start point
            r = float(self.dlg.dist_lim_text) * 1e3 # Get boundary distance (convert to meters)
            sel_ix = self.dlg.comboBox.currentIndex() # Get the selected layer index
            vl11 = self.iface.legendInterface().layers()[sel_ix] # Get the selected layer
            vl = QgsVectorLayer("LineString" + crs_string, "Road Network Information", "memory") # Layer containing road vectors
            QgsMapLayerRegistry.instance().addMapLayer(vl, False) # Hide this layer
            rni_ml = QgsMapCanvasLayer(vl)
            rni_ml.setVisible(False)
            layer_set.append(rni_ml)
            self.iface.mapCanvas().refresh()
            self.setup_polylines(vl, vl11) # Extract road vectors
            
            vl3 = QgsVectorLayer("Point" + crs_string, "Area of Availability Boundary", "memory") # Layer containing boundary points
            QgsMapLayerRegistry.instance().addMapLayer(vl3)
            vl3_ml = QgsMapCanvasLayer(vl3)
            layer_set.insert(0, vl3_ml)
            progress.setValue(15)
            self.distance(vl, start_point, vl3, r, progress) # Compute boundary
            self.iface.mapCanvas().setLayerSet(layer_set)

            self.iface.mapCanvas().refresh() # Refresh canvas
            progress.setValue(100)
            self.dlg.comboBox.clear()
            self.iface.messageBar().clearWidgets()
            self.iface.messageBar().pushSuccess("Finished!", "Completed boundary calculation. :^)")

    def setup_polylines(self, vl, vl11):
        iterr = vl11.getFeatures()
        prp = vl.dataProvider()
        vl.startEditing()
        feats = list()
        for feature in iterr:
            geom = feature.geometry()
            if geom.type() == QGis.Line:
                ln = geom.asPolyline()
                lngeom = QgsGeometry.fromPolyline(ln)
                feature = QgsFeature()
                feature.setGeometry(lngeom)
                feats.append(feature)
        prp.addFeatures(feats)
        vl.updateExtents()

    def output_img(self, extent_layer):
        rect = extent_layer.extent()
        rect.grow(5e-2)
        canvas = self.iface.mapCanvas()
        canvas.setExtent(rect)
        canvas.setLayerSet(list(map(lambda ll: QgsMapCanvasLayer(ll), QgsMapLayerRegistry.instance().mapLayers())))
        canvas.refresh()
        settings = canvas.mapSettings()
        settings.setLayers(list(map(lambda li: li.id(), QgsMapLayerRegistry.instance().mapLayers())))
        ndpi = 300.00
        dpmm = ndpi / 25.4
        nwidth = int(dpmm * settings.outputSize().width())
        nheight = int(dpmm * settings.outputSize().height())
        settings.setOutputDpi(ndpi)
        settings.setOutputSize(QSize(nwidth, nheight))
        job = QgsMapRendererParallelJob(settings)
        job.start()
        job.waitForFinished()
        image = job.renderedImage()
        image.save(self.get_files(type_="tif")[0])

    def get_files(self, type_="shp"):
        types = {"shp": "SHP files (*.shp)",
                 "tif": "TIF files (*.tif)",
                 "all": "All Files (*.*)"}
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setFilter(types[type_])
        filenames = list()
        if dlg.exec_():
            filenames = list(map(lambda ff: ".".join([ff, type_]), dlg.selectedFiles()))
        return filenames
            
    def distance(self, vl, pStart, vl3, r, progress):
        canvas = self.iface.mapCanvas()
        mapRenderer = QgsMapRenderer()
        # Set up objects for graph creation:
        director = QgsLineVectorLayerDirector(vl, -1, '', '', '', 3) # 1=direct, 2=reverse, 3=both
        properter = QgsDistanceArcProperter() # Strategy for detecting edge properties
        director.addProperter(properter)

        pr = vl3.dataProvider() # Data provider to get the boundary points
        vl3.startEditing()

        crs = mapRenderer.destinationCrs() # Gets the CRS
        builder = QgsGraphBuilder(crs)

        tiedPoints = director.makeGraph(builder, [pStart]) # Tie start point to graph
        progress.setValue(progress.value() + 15)
        graph = builder.graph()
        tStart = tiedPoints[0]

        idStart = graph.findVertex(tStart) # Vertex ID of start point
        (tree, cost) = QgsGraphAnalyzer.dijkstra(graph, idStart, 0) # Perform Dijkstra's algorithm, 
                                                                    # returns [index of incoming edge,
                                                                    # distance from root to vertex]
        progress.setValue(progress.value() + 20)

        # Get the boundary points
        upperBound = list()
        for i in range(len(cost)):
            if cost[i] > r and tree[i] != -1: # If (cost[i] > r) and the incoming vertex is not accessible,
                outVertexId = graph.arc(tree [i]).outVertex() # This is an outer vertex, so get the ID
                if cost[outVertexId] < r: # And if the source vertex is accessible,
                    upperBound.append(i) # This is an upper boundary, so we keep it.
            progress.setValue(progress.value() + 2)
        
        # Store the set of upper bound points as features
        feats = list()
        for ix in upperBound:
            centerPoint = graph.vertex(ix).point()
            newPt = QgsGeometry.fromPoint(centerPoint)
            feature = QgsFeature()
            feature.setGeometry(newPt)
            feats.append(feature)
        pr.addFeatures(feats)
        vl3.updateExtents()
        # vl.commitChanges()
        # vl3.commitChanges()



            



