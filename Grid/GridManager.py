from pivy import coin
import FreeCADGui as Gui
import FreeCAD as App
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."

from Utils import Constants

# todo: add to preferences!
_gridSpacing = Constants.gridSquareSize
_gridExtent = Constants.gridSize
_showGrid = True

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
        internalExtent = round(_gridExtent/_gridSpacing)*_gridSpacing

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
            coin.SbVec3f(0, -internalExtent, 0),
            coin.SbVec3f(0, internalExtent, 0)
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
        for i in range(-internalExtent, internalExtent, _gridSpacing):
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
    try:
        document.Name
    except: # document was deleted
        return False
    
    if not showOveride and not _showGrid:
        return False

    for grid in grids.copy():
        keepGrid = False # have these here for the best amount of reliability
        
        try:
            if hasattr(grid, "document") and grid.document != None:
                if grid.document.Name == document.Name:
                    return False
                
                keepGrid = True
            else:
                keepGrid = False
        except:
            keepGrid = True
        
        if not keepGrid:
            grids.remove(grid)

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
            pass

def showAllGrids():
    for grid in grids:
        try:
            grid.showGrid()
        except:
            pass

def removeDocument(document):
    for grid in grids:
        try:
            grid.hideGrid()
        except:
            pass

        try:
            grid.document.Name
        except:
            grids.remove(grid)
            continue

        if grid.document.Name == document.Name:
            grids.remove(grid)
            break