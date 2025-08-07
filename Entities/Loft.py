import FreeCAD as App
import FreeCADGui as Gui
import Part
import sys
import os
import json
import string
import random
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from Utils.Utils import addElementToCompoundArray, getP2PDistanceAlongNormal, generateHashName, getParent
from Utils.Constants import *
from Entities.Feature import Feature
from PySide import QtWidgets
from Utils.GuiUtils import SelectorWidget
from Utils.SketchUtils import getIDDict
import copy

class LoftTaskPanel:
    def __init__(self, obj):
        self.form = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout(self.form)
        self.layout.addWidget(QtWidgets.QLabel("Editing: " + obj.Label))
        self.extrusion = obj
        self.activeLayouts = []
        self.container = self.extrusion.Proxy.getContainer(self.extrusion)

        button_layout = QtWidgets.QHBoxLayout()
        self.applyButton = QtWidgets.QPushButton("Apply")
        self.updateButton = QtWidgets.QPushButton("Update")
        self.cancelButton = QtWidgets.QPushButton("Cancel")

        button_layout.addWidget(self.applyButton)
        button_layout.addWidget(self.updateButton)
        button_layout.addWidget(self.cancelButton)

        self.layout.addLayout(button_layout)
        
        self.applyButton.clicked.connect(self.accept)
        self.updateButton.clicked.connect(self.update)
        self.cancelButton.clicked.connect(self.reject)

        self.dimensionTypeComboLayout = QtWidgets.QHBoxLayout()
        self.dimensionTypeLabel = QtWidgets.QLabel("Type:")
        self.dimensionTypeCombo = QtWidgets.QComboBox()
        self.dimensionTypeComboLayout.setContentsMargins(0, 5, 0, 0)

        self.oldType = obj.DimensionType

        for type in dimensionTypes:
            self.dimensionTypeCombo.addItem(type, type)
        
        self.dimensionTypeCombo.setCurrentIndex(dimensionTypes.index(obj.DimensionType))

        self.dimensionTypeComboLayout.addWidget(self.dimensionTypeLabel)
        self.dimensionTypeComboLayout.addWidget(self.dimensionTypeCombo)
        self.layout.addLayout(self.dimensionTypeComboLayout)

        self.blindDimensionWidget = self.createBlindDimension()
        self.selectorWidget = self.createUTEDimension()
        self.updateGuiDimensionType()

        self.dimensionTypeCombo.currentIndexChanged.connect(self.dimensionTypeChanged)
        self.layout.addWidget(self.selectorWidget)
        self.layout.addWidget(self.blindDimensionWidget)

        # Starting offset section start
        self.startingOffsetLayout = QtWidgets.QVBoxLayout()
        self.startingOffsetComboRow = QtWidgets.QHBoxLayout()
        self.offsetLabel = QtWidgets.QLabel("Starting Offset Type:")
        self.startOffsetCombo = QtWidgets.QComboBox()
        self.startingOffsetComboRow.setContentsMargins(0, 5, 0, 0)
        self.oldStartingOffsetType = obj.StartingOffsetType
        self.oldStartingOffsetEnabled = obj.StartingOffset
        self.oldStartingOffsetLength = obj.StartingOffsetLength
        self.oldStartingOffsetUTE = obj.StartingOffsetUpToEntity

        self.sOffestBlindWidget = self.createSOffsetBlind()
        self.sOffsetSelectorWidget = self.createSOffsetUTE()

        self.startingOffsetComboRow.addWidget(self.offsetLabel)
        self.startingOffsetComboRow.addWidget(self.startOffsetCombo)
        self.startingOffsetLayout.addLayout(self.startingOffsetComboRow)
        self.startingOffsetLayout.addWidget(self.sOffestBlindWidget)
        self.startingOffsetLayout.addWidget(self.sOffsetSelectorWidget)

        self.layout.addLayout(self.startingOffsetLayout)

        self.startOffsetCombo.addItem("None", "None")
        for type in startingOffsetTypes:
            self.startOffsetCombo.addItem(type, type)
        
        self.startOffsetCombo.currentIndexChanged.connect(self.offsetTypeChanged)

        if self.extrusion.StartingOffset:
            self.startOffsetCombo.setCurrentIndex(startingOffsetTypes.index(obj.StartingOffsetType) + 1)
        else:
            self.startOffsetCombo.setCurrentIndex(0)
        
        self.updateGuiStartingOffset()
        # Starting offset section end
    
    def createSOffsetUTE(self):
        widget = SelectorWidget(container=self.container, startSelection=[self.extrusion.StartingOffsetUpToEntity], sizeLimit=1)
        return widget
    
    def createSOffsetBlind(self):
        self.sOffestBlindWidget = QtWidgets.QWidget()
        self.sOffestBlindLayout = QtWidgets.QHBoxLayout()
        self.sOffestBlindLayout.setContentsMargins(10, 0, 0, 0)
        self.sOffsetBlindLabel = QtWidgets.QLabel("Starting Offset Length:")
        self.sOffsetBlindInput = QtWidgets.QDoubleSpinBox()
        self.sOffsetBlindInput.setMinimum(-100000)
        self.sOffsetBlindInput.setMaximum(100000)
        self.sOffsetBlindInput.setSingleStep(1)
        self.sOffsetBlindInput.setValue(self.oldStartingOffsetLength)

        self.sOffestBlindLayout.addWidget(self.sOffsetBlindLabel)
        self.sOffestBlindLayout.addWidget(self.sOffsetBlindInput)
        self.sOffestBlindWidget.setLayout(self.sOffestBlindLayout)

        return self.sOffestBlindWidget
    
    def createUTEDimension(self):
        widget = SelectorWidget(container=self.container, startSelection=[self.extrusion.UpToEntity], sizeLimit=1)
        return widget

    def createBlindDimension(self):
        self.oldLength = self.extrusion.Length

        widget = QtWidgets.QWidget()
        self.blindDimensionRow = QtWidgets.QHBoxLayout()
        self.blindLabel = QtWidgets.QLabel("Length:")
        self.blindInput = QtWidgets.QDoubleSpinBox()
        self.blindInput.setMinimum(-100000)
        self.blindInput.setMaximum(100000)
        self.blindInput.setSingleStep(1)
        self.blindDimensionRow.setContentsMargins(10, 0, 0, 0)
        self.blindInput.setValue(self.oldLength)

        self.blindDimensionRow.addWidget(self.blindLabel)
        self.blindDimensionRow.addWidget(self.blindInput)
        self.blindDimensionRow.addStretch()

        widget.setLayout(self.blindDimensionRow)

        return widget
    
    def offsetTypeChanged(self, index):
        newType = self.startOffsetCombo.itemData(index)

        if newType == "None":
            self.extrusion.StartingOffset = False
        else:
            self.extrusion.StartingOffset = True
            self.extrusion.StartingOffsetType = newType
        
        self.updateGuiStartingOffset()
    
    def dimensionTypeChanged(self, index):
        newType = self.dimensionTypeCombo.itemData(index)
        self.extrusion.DimensionType = newType

        self.updateGuiDimensionType()
    
    def updateGuiStartingOffset(self):
        if self.extrusion.StartingOffset:
            if self.extrusion.StartingOffsetType == "Blind":
                self.sOffestBlindWidget.show()
                self.sOffsetSelectorWidget.hide()
                self.sOffsetSelectorWidget.toggleSelections(False)
            elif self.extrusion.StartingOffsetType == "UpToEntity":
                self.sOffestBlindWidget.hide()
                self.sOffsetSelectorWidget.show()
                self.sOffsetSelectorWidget.toggleSelections(True)
        else:
            self.sOffestBlindWidget.hide()
            self.sOffsetSelectorWidget.hide()
            self.sOffsetSelectorWidget.toggleSelections(False)
    
    def updateGuiDimensionType(self):
        if self.extrusion.DimensionType == "Blind":
            self.selectorWidget.hide()
            self.selectorWidget.toggleSelections(False)
            
            self.blindDimensionWidget.show()
                
        elif self.extrusion.DimensionType == "UpToEntity":
            self.blindDimensionWidget.hide()
            Gui.Selection.clearSelection()

            self.selectorWidget.toggleSelections(True)
            self.selectorWidget.show()

            self.oldUpToEntity = self.extrusion.UpToEntity

    def update(self):
        if self.extrusion.DimensionType == "Blind":
            self.extrusion.Length.Value = self.blindInput.value()
        elif self.extrusion.DimensionType == "UpToEntity":
            selection = self.selectorWidget.getSelection()

            if len(selection) != 0:
                self.extrusion.UpToEntity = selection[0]
        
        if self.extrusion.StartingOffset:
            if self.extrusion.StartingOffsetType == "Blind":
                self.extrusion.StartingOffsetLength = self.sOffsetBlindInput.value()
            elif self.extrusion.StartingOffsetType == "UpToEntity":
                selection = self.sOffsetSelectorWidget.getSelection()

                if len(selection) != 0:
                    self.extrusion.StartingOffsetUpToEntity = selection[0]

        self.container.recompute()
    
    def accept(self):
        self.update()

        self.selectorWidget.cleanup()
        self.sOffsetSelectorWidget.cleanup()

        Gui.Control.closeDialog()

    def reject(self):
        if hasattr(self, "oldLength"):
            self.extrusion.Length.Value = self.oldLength
        if hasattr(self, "oldUpToEntity"):
            self.extrusion.UpToEntity = self.oldUpToEntity

        self.extrusion.DimensionType = self.oldType
        self.extrusion.StartingOffset = self.oldStartingOffsetEnabled
        self.extrusion.StartingOffsetType = self.oldStartingOffsetType
        self.extrusion.StartingOffsetLength = self.oldStartingOffsetLength
        self.extrusion.StartingOffsetUpToEntity = self.oldStartingOffsetUTE

        # self.container.recompute()

        self.selectorWidget.cleanup()
        self.sOffsetSelectorWidget.cleanup()

        Gui.Control.closeDialog()

    def getStandardButtons(self):
        return 0

    def getTitle(self):
        return "Extrusion Task Panel"

    def IsModal(self):
        return False

class Loft(Feature):
    def __init__(self, obj):
        obj.Proxy = self
        self.updateProps(obj)
        
    def updateProps(self, obj):
        super(Loft, self).updateProps(obj)

        if not hasattr(obj, "Boundary"):
            obj.addProperty("App::PropertyXLink", "Boundary", "ConstraintDesign")
            obj.setEditorMode("Boundary", 3)
        
        if not hasattr(obj, "Supports"):
            obj.addProperty("App::PropertyLinkList", "Supports", "ConstraintDesign", "Support objects (ex: Two sketches)")
        
        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "Loft"
        
        if not hasattr(obj, "Group"):
            obj.addProperty("App::PropertyLinkList", "Group", "ConstraintDesign", "Group")
        
    def showGui(self, obj):
        Gui.Control.showDialog(LoftTaskPanel(obj))

    def setBoundary(self, obj, boundary):
        obj.Boundary = boundary

        self.addObject(obj, boundary)
    
    def addObject(self, obj, newObj):
        if hasattr(obj, "Group"):
            group = obj.Group
            group.append(newObj)

            obj.Group = group
    
    def getBoundaries(self, obj, isShape=False):
        if isShape:
            return [obj.Boundary.Shape]
        else:
            return [obj.Boundary]
        
    def setSupports(self, obj, supports):
        obj.Supports = supports

        for support in supports:
            self.addObject(obj, support)
    
    def getContainer(self, obj):
        return super(Loft, self).getContainer(obj)

    def makeIdentifer(self, id = "0:1:2:3:", elementType="Edge", boundaryType="Sketch", supportName="Sketch001"):
        return f"{str(id)};{elementType};{boundaryType};{supportName}"

    def identifierIsSame(self, obj, identifier1, identifier2, allSupport1IDs, allSupport2IDs):
        if identifier1 == identifier2: # avoid heavy computation if its not necessary
            return True
        
        useDualCheck = True

        identifier1Array = identifier1.split(";")
        identifier2Array = identifier2.split(";")
        identifier1GeoIDs = identifier1Array[0].split(":")
        identifier2GeoIDs = identifier2Array[0].split(":")

        identifier1Support1IDs = []
        identifier1Support2IDs = []
        identifier2Support1IDs = []
        identifier2Support2IDs = []

        for id in identifier1GeoIDs:
            if id.startswith(f"{obj.Supports[0].Name}_"): identifier1Support1IDs.append(id)
            if id.startswith(f"{obj.Supports[1].Name}_"): identifier1Support2IDs.append(id)
        
        for id in identifier2GeoIDs:
            if id.startswith(f"{obj.Supports[0].Name}_"): identifier2Support1IDs.append(id)
            if id.startswith(f"{obj.Supports[1].Name}_"): identifier2Support2IDs.append(id)
        
        if len(identifier2Support1IDs) == 0 or len(identifier2Support2IDs) == 0 or len(set(allSupport1IDs) & set(identifier2Support1IDs)) == 0 or len(set(allSupport2IDs) & set(identifier2Support2IDs)):
            useDualCheck = False
        else:
            print(f"id2: {identifier2}")

        support1Occurences = 0
        support2Occurences = 0

        if useDualCheck:
            support1Occurences = len(set(identifier1Support1IDs) & set(identifier2Support1IDs))
            support2Occurences = len(set(identifier1Support2IDs) & set(identifier2Support2IDs))

        if ((identifier1Array[1:] == identifier2Array[1:]) and ((useDualCheck and support1Occurences >= 1 and support2Occurences >= 1) or (not useDualCheck and len(set(identifier1GeoIDs) & set(identifier2GeoIDs)) >= 1))):
            return True
        else:
            return False

    # Format {"HashName": {"Element:" edge, "Stale": <True/False>, "Identifier": "GeoId;ElType<V(1/2)>;<Sketch/Wires>;SupportName;"}}
    def updateElement(self, obj, element, identifier, map, allSupport1IDs = None, allSupport2IDs = None, complexCheck=False):
        hasElement = False

        for key, value in map.items():
            if (complexCheck == False and value["Identifer"] == identifier) or (complexCheck == True and self.identifierIsSame(obj, identifier, value["Identifer"], allSupport1IDs, allSupport2IDs)):
                map[key]["Element"] = str(element[0].Name) + "." + str(element[1])
                map[key]["Identifer"] = identifier
                map[key]["Stale"] = False

                hasElement = True

        if hasElement == False:
            hash = generateHashName(map)

            map[hash] = {"Element": str(element[0].Name) + "." + str(element[1]), "Stale": False, "Identifer": identifier}
        
        return map
    
    def getSupports(self, obj):
        if hasattr(obj, "Supports") and len(obj.Supports) != 0:
            return obj.Supports
        else:
            return []
    
    def generateShape(self, obj, prevShape):
        self.updateProps(obj)

        outerWires = []
        innerWires = []

        container = getParent(obj, "PartContainer")

        for support in obj.Supports:
            if hasattr(container, "Group") and support not in container.Group:
                App.Console.PrintError(f"{support.Label} not in {container.Label}!\nOne or both of your supports is not setup properly!\n")
                return prevShape

            support.Proxy.updateSketch(support, container)
            
            wires = support.Shape.Wires

            if len(wires) == 0:
                raise Exception(f"{support.Label} needs a closed wire!\n")
            
            sortedWires = sorted(wires, key=lambda w: abs(Part.Face(w).Area), reverse=True)
            outerWires.append(sortedWires[0])
            innerWires.extend(sortedWires[1:])
        
        outerShape = Part.Shape()
        innerShape = Part.Shape()

        if len(outerWires) == 2:
            outerShape = Part.makeLoft(outerWires, True)
        else:
            raise Exception("Not enough wires to create a loft!\n This could mean that one of your sketches has no geometry, or it means that the geometry doesn't close into a wire!\n")
        
        if len(innerWires) == 2:
            innerShape = Part.makeLoft(innerWires, True)

        finalShape = outerShape.copy()

        if not finalShape.isNull() and not innerShape.isNull():
            finalShape = finalShape.cut(innerShape)
        
        try:
            elementMap = json.loads(obj.ElementMap)
        except:
            raise Exception("The Element Map is an invalid json string!")

        # {"g<num>v<1/2>": Vector}
        points = {}
        geoType = ""
        identifierList = []
        support1GeoIDList = []
        support2GeoIDList = []

        startTime = time.time()
        boundaryElementList = []
        boundaryEdgesList = []
        boundaryVertexesList = []

        for supportNum, sketch in enumerate(obj.Supports):
            idList = getIDDict(sketch)

            for id,geo in idList.items():
                geoShape = geo.toShape()
                sketchIndexEdges = len(boundaryEdgesList)
                sketchIndexVertices = len(boundaryVertexesList)

                newShape = geoShape.copy()
                newShape.Placement.Base = (newShape.Placement.Base + (sketch.Placement.Base))
                newShape.Placement.Rotation = sketch.Placement.Rotation

                if isinstance(geoShape, Part.Edge):
                    element = (obj.Boundary, "Edge" + str(sketchIndexEdges + 1))

                    geoType = "Edge"

                    for i, vt in enumerate(newShape.Vertexes):
                        geoID = f"{sketch.Name}_{str(id)}v{str(i + 1)}"

                        points[geoID] = vt.Point
                        if supportNum == 0:
                            support1GeoIDList.append(geoID)
                        else:
                            support2GeoIDList.append(geoID)
                    
                elif isinstance(geoShape, Part.Vertex):
                    element = (obj.Boundary, "Vertex" + str(sketchIndexVertices + 1))
                    geoID = f"{sketch.Name}_{str(id)}"

                    geoType = "Vertex"
                    points[geoID] = newShape.Point
                    if supportNum == 0:
                        support1GeoIDList.append(geoID)
                    else:
                        support2GeoIDList.append(geoID)
                
                addElementToCompoundArray(newShape, boundaryElementList, boundaryEdgesList, boundaryVertexesList)
                
                identifier = self.makeIdentifer(str(id), geoType, "Sketch", sketch.Name)
                identifierList.append(identifier)

                elementMap = self.updateElement(obj, element, identifier, elementMap)
        
        tol = 1e-3

        for i, edge in enumerate(finalShape.Edges):
            # avoid another for loop for better speed
            distance1 = getP2PDistanceAlongNormal(obj.Supports[0].Placement.Base, edge.CenterOfMass, obj.Supports[0].Placement.Rotation.multVec(App.Vector(0, 0, 1)))
            distance2 = getP2PDistanceAlongNormal(obj.Supports[1].Placement.Base, edge.CenterOfMass, obj.Supports[1].Placement.Rotation.multVec(App.Vector(0, 0, 1)))

            # could cause issues with really small lofts, but i dont really care right now
            if abs(distance1) > tol and abs(distance2) > tol:
                idsArray = []

                # ignore what i said about for loops earlier
                for geoId, pt in points.items():
                    if pt.isEqual(edge.Vertexes[0].Point, 1e-5):
                        idsArray.append(f"{geoId}")
                    
                    if pt.isEqual(edge.Vertexes[1].Point, 1e-5):
                        idsArray.append(f"{geoId}")
                
                    
                if len(idsArray) != 0:
                    idString = ":".join(idsArray)

                    addElementToCompoundArray(edge.copy(), boundaryElementList, boundaryEdgesList, boundaryVertexesList)

                    element = (obj.Boundary, "Edge" + str(len(boundaryEdgesList)))
                    identifier = self.makeIdentifer(idString, "Edge", "WiresDatum", "")
                    identifierList.append(identifier)

                    elementMap = self.updateElement(obj, element, identifier, elementMap, support1GeoIDList, support2GeoIDList, True)
            
        App.Console.PrintLog(obj.Label + " update datums time: " + str(time.time() - startTime) + "\n")
        
        for hash, value in elementMap.copy().items():
            if value["Identifer"] not in identifierList:
                # elementMap.pop(hash)
                elementMap[hash]["Stale"] = True

        obj.ElementMap = json.dumps(elementMap)
        
        # obj.Boundary.Placement = obj.Supports[0].Placement
        obj.Boundary.Shape = Part.Compound(boundaryElementList)
        obj.Boundary.ViewObject.LineWidth = boundaryLineWidth
        obj.Boundary.ViewObject.PointSize = boundaryPointSize
        obj.Boundary.Visibility = True
        obj.Boundary.purgeTouched()

        for sketch in obj.Supports:
            sketch.Visibility = False

        obj.IndividualShape = finalShape

        if not prevShape.isNull():
            if obj.Remove:
                finalShape = prevShape.cut(finalShape)
            else:
                finalShape = prevShape.fuse(finalShape)

        obj.Shape = finalShape

        return finalShape

    def execute(self, obj):
        if obj.Group == []:
            obj.Group = [obj.Boundary].extend(obj.Supports)

        self.updateProps(obj)
            
    def onChanged(self, obj, prop):
        super(Loft, self).onChanged(obj, prop)
            
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None

class ViewProviderExtrusion:
    def __init__(self, obj):
        obj.Proxy = self
        obj.Selectable = False
        self.Origin = None
    
    def onDelete(self, vobj, subelements):
        if hasattr(vobj.Object, "Boundary"):
            if vobj.Object.Boundary != None:
                vobj.Object.Document.removeObject(vobj.Object.Boundary.Name)

        return True
    
    def attach(self, vobj):
        # Called when the view provider is attached
        self.Object = vobj
        self.Object.Selectable = False

        return

    def setEdit(self, vobj, mode):
        vobj.Object.Document.openTransaction("EditExtrusion")
        vobj.Object.Proxy.showGui(vobj.Object)

        return False

    def unsetEdit(self, vobj, mode):
        return True

    def updateData(self, fp, prop):
        # Called when a property changes
        return

    def getDisplayModes(self, vobj):
        # Available display modes
        return ["Flat Lines", "Shaded"]

    def getDefaultDisplayMode(self):
        # Default display mode
        return "Flat Lines"

    def setDisplayMode(self, mode):
        # Called when the display mode changes
        return mode

    def onChanged(self, vobj, prop):
        # Called when a property of the viewobject changes
        return

    def getIcon(self):
        return os.path.join(os.path.dirname(__file__), "..", "icons", "Extrusion.svg")
    
    def claimChildren(self):
        # App.Console.PrintMessage('claimChildren called\n')
        if hasattr(self, "Object") and hasattr(self.Object.Object, "Group"):
            return self.Object.Object.Group
        return []

    def dragObject(self, obj):
        App.Console.PrintMessage(obj)

    def __getstate__(self):
        # Called when saving
        return None

    def __setstate__(self, state):
        # Called when restoring
        return None
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None
    
def makeLoft():
    activeObject = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")

    if activeObject != None and hasattr(activeObject, "Type") and activeObject.Type == "PartContainer":
        selectedObjects = Gui.Selection.getSelection()
        doc = activeObject.Document
        doc.openTransaction("CreateExtrusion")

        if len(selectedObjects) == 2:
            obj = doc.addObject("Part::FeaturePython", "Loft")
            boundary = doc.addObject("Part::Feature", "Boundary")
            boundary.addProperty("App::PropertyString", "Type")
            boundary.Type = "Boundary"

            Loft(obj)
            ViewProviderExtrusion(obj.ViewObject)

            obj.Proxy.setSupports(obj, selectedObjects)
            obj.Proxy.setBoundary(obj, boundary)

            activeObject.Proxy.addObject(activeObject, obj, True)
            activeObject.Proxy.setTip(activeObject, obj)
        else:
            App.Console.PrintError("Selected object is not a sketch!\n")
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")
