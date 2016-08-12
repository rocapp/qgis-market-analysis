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

canvas.setExtent(vl2.extent())
# clayers = list(map(lambda clay: QgsMapCanvasLayer(clay), 
#             QgsMapLayerRegistry.instance().mapLayers().values()))
canvas.setLayerSet([vl_, vl2_])

mapRenderer = QgsMapRenderer()
# mapRenderer.setDestinationCrs(crs)
mapRenderer.setProjectionsEnabled(True)

c = QgsComposition(mapRenderer)
c.setPlotStyle(QgsComposition.Print)

dpi = c.printResolution()
dpmm = dpi / 25.4
width = int(dpmm * c.paperWidth())
height = int(dpmm * c.paperHeight())

composerMap = QgsComposerMap(c, 0, 0, c.paperWidth(), c.paperHeight())
composerMap.hasFrame()
c.addItem(composerMap)

img = QImage(QSize(width, height), QImage.Format_ARGB32)
color = QColor(255, 255, 255)
img.fill(color.rgb())

# img_painter = QPainter()
# img_painter.begin(img)
# img_painter.setRenderHint(QPainter.Antialiasing)
canvas.refresh()

###################################

def distance():
  director = QgsLineVectorLayerDirector(vl, -1, '', '', '', 3)
  properter = QgsDistanceArcProperter()
  director.addProperter(properter)

  crs = mapRenderer.destinationCrs()
  builder = QgsGraphBuilder(crs)

  pStart = QgsPoint(-83.94216704, 34.53197821)
  # crsSrc = QgsCoordinateReferenceSystem(4326)
  # xform = QgsCoordinateTransform(crsSrc, crs)
  # pStart = xform.transform(pStart)
  print pStart
  delta = canvas.getCoordinateTransform().mapUnitsPerPixel() * 1

  rb1 = QgsRubberBand(canvas)
  rb1.setIconSize(100)
  # rb1.setIconType(QgsVertexMarker.ICON_X)
  # rb1.setPenWidth(50)
  # rb1.setCenter(QgsPoint(pStart.x(), pStart.y()))
  rb1.setToGeometry(QgsGeometry.fromPolyline([QgsPoint(pStart.x(), pStart.y())]), None)
  rb1.setColor(Qt.red)
  c.addItem(rb1)
  # canvas.scene().addItem(rb1)
  if hasattr(vl, "setCacheImage"):
    vl.setCacheImage(None)
  vl.triggerRepaint()

  feat = QgsFeature(vl.pendingFields())
  feat.setGeometry(rb1.asGeometry())
  (res, outFeats) = vl.dataProvider().addFeatures([feat])
  vl.updateFields()

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

  for i in upperBound:
    centerPoint = graph.vertex(i).point()
    rb = QgsRubberBand(canvas)
    rb.setIconSize(10)
    # rb.setIconType(QgsVertexMarker.ICON_BOX)
    # rb.setPenWidth(5)
    rb.setColor(Qt.red)
    # rb.setCenter(QgsPoint(centerPoint.x(), centerPoint.y()))
    rb.addPoint(QgsPoint(centerPoint.x() - delta, centerPoint.y() - delta))
    rb.addPoint(QgsPoint(centerPoint.x() + delta, centerPoint.y() - delta))
    rb.addPoint(QgsPoint(centerPoint.x() + delta, centerPoint.y() + delta))
    rb.addPoint(QgsPoint(centerPoint.x() - delta, centerPoint.y() + delta))
    rb.setToGeometry(QgsGeometry.fromPolyline([QgsPoint(centerPoint.x(), centerPoint.y())]), None)
    feat = QgsFeature(vl.pendingFields())
    feat.setGeometry(rb.asGeometry())
    (res, outFeats) = vl.dataProvider().addFeatures([feat])
    vl.updateFields()
    c.addItem(rb)
  canvas.refresh()
  c.refreshItems()
  canvas.zoomToFullExtent()
  canvas.refresh()
  canvas.saveAsImage("Render2.png")
  # def exportMap():
  #   vl_.setVisible(False)
  #   canvas.refresh()
  #   canvas.setLayerSet([vl_, vl2_])
  #   canvas.saveAsImage("Render1.png")
  #   qgs.exitQgis()
  #   qgs.exit()
  # QTimer.singleShot(1000, exportMap)
  # writer = QgsVectorFileWriter("C://Users//Robbie//Desktop//", "System", vl.fields(), QGis.WKBLineString, None, "ESRI Shapefile")
  # if writer.hasError() != QgsVectorFileWriter.NoError:
  #   print "Error when creating shapefile: ",  writer.errorMessage()
  # error = QgsVectorFileWriter.writeAsVectorFormat(vl, "C://Users//Robbie//Desktop//DrivingDistance.shp",
  #                                                  "System", None, "ESRI Shapefile")
  # if error == QgsVectorFileWriter.NoError:
  #   print "success!"

distance()
rlayers = QgsMapLayerRegistry.instance().mapLayers().keys()
mapRenderer.setLayerSet([vl2.id()])
clayers = list(map(lambda clay: QgsMapCanvasLayer(clay), 
            QgsMapLayerRegistry.instance().mapLayers().values()))
canvas.setLayerSet([vl2_])
rect = QgsRectangle(mapRenderer.fullExtent())
rect.scale(1.1)
mapRenderer.setExtent(rect)
mapRenderer.setOutputSize(img.size(), img.logicalDpiX())
# mapRenderer.render(img_painter)
# sourceArea = QRectF(0, 0, c.paperWidth(), c.paperHeight())
# targetArea = QRectF(0, 0, width, height)
# c.render(img_painter, targetArea, sourceArea)
# img_painter.end()
c.exportAsPDF("Render.pdf")
# img.save("C:\Users\Robbie\Desktop\Render.png","png")
# c.save("C:\Users\Robbie\Desktop\Render2.png","png")
# print(QgsMapLayerRegistry.instance().mapLayers(), len(QgsMapLayerRegistry.instance().mapLayers()))
print("Done")
qgs.exec_()
qgs.exitQgis()