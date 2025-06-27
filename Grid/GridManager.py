from pivy import coin
import FreeCADGui as Gui
import FreeCAD as App

# todo: add to preferences!
gridSpacing = 30
gridExtent = 10_000
showGrid = True

grids = []

class Grid:
    def __init__(self, document):
        self.gridRoot = None
        self.document = document
        self.sceneGraph = None
    
    def showGrid(self):
        if self.gridRoot != None:
            if self.sceneGraph == None:
                self.sceneGraph = Gui.getDocument(self.document.Name).ActiveView.getSceneGraph()
            
            self.sceneGraph.addChild(self.gridRoot)
    
    def hideGrid(self):
        if self.gridRoot != None:
            if self.sceneGraph == None:
                self.sceneGraph.removeChild(self.gridRoot)

    def createGrid(self):
        internalExtent = round(gridExtent/gridSpacing)*gridSpacing

        self.gridRoot = coin.SoSeparator()

        gridColor = coin.SoBaseColor()
        gridColor.rgb = (0.7, 0.7, 0.7)

        gridDrawStyle = coin.SoDrawStyle()
        gridDrawStyle.lineWidth = 1

        gridCoords = coin.SoCoordinate3()
        gridLines = coin.SoLineSet()

        self.gridRoot.addChild(gridColor)
        self.gridRoot.addChild(gridDrawStyle)
        self.gridRoot.addChild(gridCoords)
        self.gridRoot.addChild(gridLines)

        xAxisSep = coin.SoSeparator()

        xAxisStyle = coin.SoDrawStyle()
        xAxisStyle.lineWidth = 2

        xAxisColor = coin.SoBaseColor()
        xAxisColor.rgb = (1, 0, 0)

        xAxisCoords = coin.SoCoordinate3()
        xAxisCoords.point.setValues(0, 2, [
            coin.SbVec3f(-internalExtent, 0, 0),
            coin.SbVec3f(internalExtent, 0, 0)
        ])

        xAxisLines = coin.SoLineSet()
        xAxisLines.numVertices.setValue(2)

        xAxisSep.addChild(xAxisStyle)
        xAxisSep.addChild(xAxisColor)
        xAxisSep.addChild(xAxisCoords)
        xAxisSep.addChild(xAxisLines)
        self.gridRoot.addChild(xAxisSep)

        yAxisSep = coin.SoSeparator()

        yAxisStyle = coin.SoDrawStyle()
        yAxisStyle.lineWidth = 2

        yAxisColor = coin.SoBaseColor()
        yAxisColor.rgb = (0, 1, 0)

        yAxisCoords = coin.SoCoordinate3()
        yAxisCoords.point.setValues(0, 2, [
            coin.SbVec3f(0, -9990, 0),
            coin.SbVec3f(0, 9990, 0)
        ])

        yAxisLines = coin.SoLineSet()
        yAxisLines.numVertices.setValue(2)

        yAxisSep.addChild(yAxisStyle)
        yAxisSep.addChild(yAxisColor)
        yAxisSep.addChild(yAxisCoords)
        yAxisSep.addChild(yAxisLines)
        self.gridRoot.addChild(yAxisSep)

        points = []
        numVerts = []
        for i in range(-internalExtent, internalExtent, gridSpacing):
            points.append(coin.SbVec3f(-internalExtent, i, 0))
            points.append(coin.SbVec3f(internalExtent, i, 0))
            numVerts.append(2)

            points.append(coin.SbVec3f(i, -internalExtent, 0))
            points.append(coin.SbVec3f(i, internalExtent, 0))
            numVerts.append(2)

        gridCoords.point.setValues(0, len(points), points)
        gridLines.numVertices.setValues(0, len(numVerts), numVerts)

        return self.gridRoot

def addGrid(document, showOveride=False):
    if not showOveride and not showGrid:
        return False

    for grid in grids:
        if grid.document.Name == document.Name:
            return False

    grid = Grid(document)
    grid.createGrid()
    grid.showGrid()

    grids.append(grid)

    return True

def hideAllGrids():
    for grid in grids:
        try:
            grid.hideGrid()
        except:
            print("hiding grid failed")

def showAllGrids():
    for grid in grids:
        try:
            grid.showGrid()
        except:
            print("showing grid failed")

def removeDocument(document):
    for grid in grids:
        try:
            grid.hideGrid()
        except:
            pass

        if grid.document.Name == document.Name:
            grids.remove(grid)
            break