import sys

from qgis.core import *
from qgis.gui import *
from qgis.networkanalysis import *
import qgis.utils

from PyQt4.QtCore import *
from PyQt4.QtGui import *

###################################
QgsApplication.setPrefixPath("C:\\OSGeo4W\\apps\\qgis", True)
qgs = QgsApplication([], True)
qgs.initQgis()

crs = QgsCoordinateReferenceSystem()
crs.createFromProj4("+proj=aeqd +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs")

project = QgsProject.instance()

canvas = QgsMapCanvas() # Canvas
canvas.setCanvasColor(Qt.white)
canvas.enableAntiAliasing(True)
canvas.refresh()

bridge = QgsLayerTreeMapCanvasBridge( \
         QgsProject.instance().layerTreeRoot(), canvas)

project.read(QFileInfo("network_analysis.qgs"))

print len(QgsMapLayerRegistry.instance().mapLayers())

vl = QgsMapLayerRegistry.instance().mapLayers()[u'nodes_to_edges20160111174805104']
vl.setCrs(crs)
vl_ = QgsMapCanvasLayer(vl)
vl_.setVisible(False)
canvas.refresh()

vl2 = QgsMapLayerRegistry.instance().mapLayers()[u'DQ_area_roads20160111140922177']
vl2_ = QgsMapCanvasLayer(vl2)
vl2_.setVisible(True)
canvas.refresh()

vl3 = QgsVectorLayer()
vl3_ = QgsMapCanvasLayer(vl3)
vl3_.setVisible(True)
canvas.refresh()

canvas.setExtent(vl2.extent())
canvas.setLayerSet([vl2_, vl3_])

mapRenderer = QgsMapRenderer()
mapRenderer.setProjectionsEnabled(True)

img = QImage(QSize(width, height), QImage.Format_ARGB32)
color = QColor(255, 255, 255)
img.fill(color.rgb())

canvas.refresh()

###################################

def distance():
  director = QgsLineVectorLayerDirector(vl, -1, '', '', '', 3)
  properter = QgsDistanceArcProperter()
  director.addProperter(properter)

  crs = mapRenderer.destinationCrs()
  builder = QgsGraphBuilder(crs)

  pStart = QgsPoint(-83.94216704, 34.53197821)
  print pStart
  delta = canvas.getCoordinateTransform().mapUnitsPerPixel() * 1

  QgsGeometry.fromPoint(QgsPoint(pStart))

  tiedPoints = director.makeGraph(builder, [pStart])
  graph = builder.graph()
  tStart = tiedPoints[0]

  idStart = graph.findVertex(tStart)
  (tree, cost) = QgsGraphAnalyzer.dijkstra(graph, idStart, 0)

  upperBound = []
  r = 40000.0
  i = 0
  while i < len(cost):
    if cost[i] > r and tree[i] != -1:
      outVertexId = graph.arc(tree [i]).outVertex()
      if cost[outVertexId] < r:
        upperBound.append(i)
    i = i + 1

  dataProvider = vl3.dataProvider()
  for i in upperBound:
    centerPoint = graph.vertex(i).point()
    newPt = QgsGeometry.fromPoint(centerPoint)
    feature = QgsFeature()
    feature.setGeometry(newPt)
    dataProvider.addFeatures([feature])
  canvas.refresh()
  canvas.zoomToFullExtent()
  canvas.refresh()
  canvas.saveAsImage("Render2.png")
qgs.exec_()
qgs.exitQgis()