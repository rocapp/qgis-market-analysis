from qgis.gui import QgsMapTool
from qgis.core import QgsGeometry, QgsFeature

class PointTool(QgsMapTool):
    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.point = None
        self.label = None
        self.start_layer = None

    def set_label(self, label):
        self.label = label

    def set_start_layer(self, layer):
        self.start_layer = layer

    def canvasPressEvent(self, event):
        pass

    def canvasMoveEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()

        point = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)
        if self.label is not None and self.point is None: self.label.setText(repr(point))

    def canvasReleaseEvent(self, event):
        #Get the click
        x = event.pos().x()
        y = event.pos().y()

        point = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)

        self.point = point
        if self.label is not None: self.label.setText(repr(self.point))
        if self.start_layer is not None: self.setup_start_point()

    def setup_start_point(self):
        start_point = self.point
        start_vl = self.start_layer
        startPt = QgsGeometry.fromPoint(start_point) # Get geometry of start point
        startF = QgsFeature() # Create a new feature for the start point
        startF.setGeometry(startPt)
        pr_start = start_vl.dataProvider() # Add start point feature to layer
        start_vl.startEditing()
        pr_start.addFeatures([startF])
        start_vl.updateExtents()
        self.canvas.refresh()

    def activate(self):
        self.canvas.setMapTool(self)

    def deactivate(self):
        self.canvas.unsetMapTool(self)

    def reset(self):
        self.start_layer = None
        self.label = None
        self.point = None
        self.canvas = None

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True