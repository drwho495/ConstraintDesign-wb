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
from Commands.SketchUtils import positionSketch
from Utils import isType, getDistanceToEntity, generateHashName
from Entities.Entity import Entity
from PySide import QtWidgets
from GuiUtils import SelectorWidget
import copy

dimensionTypes = ["Blind", "UpToEntity"]
startingOffsetTypes = ["Blind", "UpToEntity"]

class ExtrusionTaskPanel:
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

        self.createBlindDimension()
        self.createUTEDimension()
        self.updateGuiDimensionType()
        self.dimensionTypeCombo.currentIndexChanged.connect(self.dimensionTypeChanged)

        # Starting offset section start
        self.startingOffsetLayout = QtWidgets.QVBoxLayout()
        self.startingOffsetComboRow = QtWidgets.QHBoxLayout()
        self.offsetLabel = QtWidgets.QLabel("Starting Offset Type:")
        self.startOffsetCombo = QtWidgets.QComboBox()
        self.startingOffsetComboRow.setContentsMargins(0, 5, 0, 0)
        self.oldStartingOffsetType = obj.StartingOffsetType
        self.oldStartingOffsetEnabled = obj.StartingOffset
        self.oldStartingOffsetLength = obj.StartingOffsetLength

        self.sOffestBlindWidget = self.createSOffsetBlind()
        self.sOffsetSelectorWidget = self.createSOffsetUTE()
        self.createUTEDimension()

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

        print(self.extrusion.DimensionType)
    
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
        self.selectorWidget = SelectorWidget(container=self.container, startSelection=[self.extrusion.UpToEntity], sizeLimit=1)
        self.layout.addWidget(self.selectorWidget)

    def createBlindDimension(self):
        self.oldLength = self.extrusion.Length

        self.blindDimensionWidget = QtWidgets.QWidget()
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

        self.blindDimensionWidget.setLayout(self.blindDimensionRow)
        self.layout.addWidget(self.blindDimensionWidget)
    
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
            self.extrusion.Length = self.blindInput.value()
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

        if self.selectorWidget != None:
            self.selectorWidget.cleanup()
        Gui.Control.closeDialog()

    def reject(self):
        if hasattr(self, "oldLength"):
            self.extrusion.Length = self.oldLength
        if hasattr(self, "oldUpToEntity"):
            self.extrusion.UpToEntity = self.oldUpToEntity

        self.extrusion.DimensionType = self.oldType

        self.container.recompute()
        if self.selectorWidget != None:
            self.selectorWidget.cleanup()
        Gui.Control.closeDialog()

    def getStandardButtons(self):
        return 0

    def getTitle(self):
        return "Extrusion Task Panel"

    def IsModal(self):
        return False

class Extrusion(Entity):
    def __init__(self, obj):
        obj.Proxy = self
        self.updateProps(obj)
        
    def updateProps(self, obj):
        if not hasattr(obj, "WiresDatum"):
            obj.addProperty("App::PropertyXLink", "WiresDatum", "ConstraintDesign")
            obj.setEditorMode("WiresDatum", 3)
        
        if not hasattr(obj, "Suppressed"):
            obj.addProperty("App::PropertyBool", "Suppressed", "ConstraintDesign", "Is feature used.")
            obj.Suppressed = False
        
        if not hasattr(obj, "SketchProjection"):
            obj.addProperty("App::PropertyXLink", "SketchProjection", "ConstraintDesign")
            obj.setEditorMode("SketchProjection", 3)
        
        if not hasattr(obj, "Support"):
            obj.addProperty("App::PropertyXLink", "Support", "ConstraintDesign", "Support object (ex: A sketch)")
        
        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "Extrusion"

        if not hasattr(obj, "DimensionType"):
            obj.addProperty("App::PropertyEnumeration", "DimensionType", "ConstraintDesign", "Determines the type of dimension that controls the length of extrusion.")
            obj.DimensionType = dimensionTypes
            obj.DimensionType = "Blind"
        
        if not hasattr(obj, "ElementMap"):
            obj.addProperty("App::PropertyString", "ElementMap", "ConstraintDesign", "The element map of this extrusion.")
            obj.ElementMap = "{}"

        if not hasattr(obj, "Symmetric"):
            obj.addProperty("App::PropertyBool", "Symmetric", "ConstraintDesign", "Determines if this extrusion will be symmetric to the extrusion plane.")
            obj.Symmetric = False

        if not hasattr(obj, "Remove"):
            obj.addProperty("App::PropertyBool", "Remove", "ConstraintDesign", "Determines the type of boolean operation to perform.")
            obj.Remove = False
        
        if not hasattr(obj, "Group"):
            obj.addProperty("App::PropertyLinkList", "Group", "ConstraintDesign", "Group")
        
        if not hasattr(obj, "Length"):
            obj.addProperty("App::PropertyFloat", "Length", "ConstraintDesign", "Length of extrusion.")
            obj.Length = 10
            
        if not hasattr(obj, "UpToEntity"):
            obj.addProperty("App::PropertyString", "UpToEntity", "ConstraintDesign")
            obj.UpToEntity = ""

        if not hasattr(obj, "StartingOffset"):
            obj.addProperty("App::PropertyBool", "StartingOffset", "ConstraintDesign", "Use Starting Offset")
            obj.StartingOffset = False
        
        if not hasattr(obj, "StartingOffsetType"):
            obj.addProperty("App::PropertyEnumeration", "StartingOffsetType", "ConstraintDesign", "Type of Starting Offset.")
            obj.StartingOffsetType = startingOffsetTypes
            obj.StartingOffsetType = "Blind"
        
        if not hasattr(obj, "StartingOffsetUpToEntity"):
            obj.addProperty("App::PropertyString", "StartingOffsetUpToEntity", "ConstraintDesign")
        
        if not hasattr(obj, "StartingOffsetLength"):
            obj.addProperty("App::PropertyFloat", "StartingOffsetLength", "ConstraintDesign")
    
    def showGui(self, obj, addOldSelection = True, startSelection = []):
        Gui.Control.showDialog(ExtrusionTaskPanel(obj))

    def setDatums(self, obj, wiresDatum, sketchProjection):
        obj.WiresDatum = wiresDatum
        obj.SketchProjection = sketchProjection

        self.addObject(obj, wiresDatum)
        self.addObject(obj, sketchProjection)
    
    def addObject(self, obj, newObj):
        if hasattr(obj, "Group"):
            group = obj.Group
            group.append(newObj)

            print("add " + newObj.Label)

            obj.Group = group
    
    def getBoundaries(self, obj, isShape=False):
        if isShape:
            return [obj.WiresDatum.Shape, obj.SketchProjection.Shape]
        else:
            return [obj.WiresDatum, obj.SketchProjection]
        
    def setSupport(self, obj, support):
        obj.Support = support

        self.addObject(obj, support)
    
    def getContainer(self, obj):
        return super(Extrusion, self).getContainer(obj)

    # Format {"HashName": {"Element:" edge, "GeoId", "ElType": Vertex/Edge, sketchGeoId, "Occurrence": 0-∞, "FeatureType": Sketch, SketchProj, WiresDatum}}
    def updateElement(self, element, id, map, elType, occurrence = 0, featureType = "Sketch"):
        hasElement = False

        for key, value in map.items():
            if value["GeoId"] == id and value["Occurrence"] == occurrence and ((value.get("ElType") == None and value["Element"].split(".")[1].startswith(element[1])) or (value.get("ElType") != None and value["ElType"] == elType)) and value["FeatureType"] == featureType:
                map[key]["Element"] = str(element[0].Name) + "." + str(element[1])
                map[key]["ElType"] = elType

                hasElement = True

        if hasElement == False:
            hash = generateHashName(map)
            
            map[hash] = {"Element": str(element[0].Name) + "." + str(element[1]), "GeoId": id, "Occurrence": occurrence, "FeatureType": featureType, "ElType": elType}
        
        return map
    
    def generateShape(self, obj, prevShape):
        self.updateProps(obj)

        if obj.Support.TypeId == "Sketcher::SketchObject" or isType(obj.Support, "BoundarySketch"):
            sketch = obj.Support

            if hasattr(sketch, "Support"):
                container = self.getContainer(obj)

                positionSketch(sketch, container)

            sketch.recompute()

            sketchWires = list(filter(lambda w: w.isClosed(), sketch.Shape.Wires))
            face = Part.makeFace(sketchWires)
            ZOffset = 0
            normal = sketch.Placement.Rotation.multVec(App.Vector(0, 0, 1))
            extrudeLength = 1

            print(obj.DimensionType)
            print(extrudeLength)

            if obj.Symmetric:
                if not obj.StartingOffset:
                    ZOffset += -extrudeLength / 2
                else:
                    App.Console.PrintWarning(f"({obj.Label}) Cannot enable symmetry and starting offset in one extrusion!\n")
                        
            if obj.StartingOffset:
                if obj.StartingOffsetType == "Blind":
                    ZOffset += obj.StartingOffsetLength
                elif obj.StartingOffsetType == "UpToEntity" and obj.StartingOffsetUpToEntity != "":
                    ZOffset += getDistanceToEntity(obj, obj.StartingOffsetUpToEntity, sketch.Placement.Base, normal)
            
            offsetVector = normal * ZOffset
            
            if obj.DimensionType == "Blind":
                extrudeLength = obj.Length
            elif obj.DimensionType == "UpToEntity" and obj.UpToEntity != "":
                extrudeLength = getDistanceToEntity(obj, obj.UpToEntity, (sketch.Placement.Base + offsetVector), normal)

            
            print("ZOffset: " + str(ZOffset))

            extrudeVector = normal * extrudeLength

            extrusion = face.extrude(extrudeVector)
            extrusion.Placement.Base = extrusion.Placement.Base + offsetVector

            if not prevShape.isNull():
                if obj.Remove:
                    extrusion = prevShape.cut(extrusion)
                else:
                    extrusion = prevShape.fuse(extrusion)
            
            obj.Shape = extrusion
            obj.SketchProjection.Shape = Part.Shape()
            obj.WiresDatum.Shape = Part.Shape()

            if not hasattr(obj, "ElementMap"):
                try:
                    self.updateProps(obj)
                except Exception as e:
                    raise Exception("Unable to create ElementMap property! Error: " + str(e))
            
            try:
                elementMap = json.loads(obj.ElementMap)
            except:
                raise Exception("The Element Map is an invalid json string!")
            
            vertexList = []
            wiresEdgeIndex = 0
            wiresVertexIndex = 0
            sketchIndexEdges = 0
            sketchIndexVertices = 0
            geoType = "Edge"
            points = []
            idList = []

            startTime = time.time()

            for geoFacade in sketch.GeometryFacadeList:
                line = Part.Shape()
                geo = geoFacade.Geometry

                idList.append(geoFacade.Id)
                
                # Handle Wires
                
                if isinstance(geo, Part.Point):
                    startPoint = App.Vector(geo.X, geo.Y, geo.Z)
                    endPoint = startPoint + App.Vector(0, 0, obj.Length)
                    
                    if startPoint not in vertexList and endPoint not in vertexList:
                        line = Part.LineSegment(startPoint, endPoint).toShape()
                        obj.WiresDatum.Shape = Part.Compound([obj.WiresDatum.Shape, line])

                        wiresEdgeIndex += 1

                        element = (obj.WiresDatum, "Edge" + str(wiresEdgeIndex))
                        elementMap = self.updateElement(element, geoFacade.Id, elementMap, "Edge", 0, "WiresDatum")
                    
                    vertexList.append(startPoint)
                    vertexList.append(endPoint)
                elif isinstance(geo, Part.LineSegment) or isinstance(geo, Part.ArcOfCircle):
                    for i, point in enumerate([geo.StartPoint, geo.EndPoint]):
                        startPoint = point
                        endPoint = point + App.Vector(0, 0, obj.Length)
                        
                        if startPoint not in vertexList and endPoint not in vertexList:
                            line = Part.LineSegment(startPoint, endPoint).toShape()
                        
                            obj.WiresDatum.Shape = Part.Compound([obj.WiresDatum.Shape, line])
                            wiresEdgeIndex += 1
                            wiresVertexIndex += 2

                            element = (obj.WiresDatum, "Edge" + str(wiresEdgeIndex))
                            elementMap = self.updateElement(element, geoFacade.Id, elementMap, "Edge", i, "WiresDatum")

                            element = (obj.WiresDatum, "Vertex" + str(wiresVertexIndex - 1))
                            elementMap = self.updateElement(element, geoFacade.Id, elementMap, "Vertex1", i, "WiresDatum")

                            element = (obj.WiresDatum, "Vertex" + str(wiresVertexIndex))
                            elementMap = self.updateElement(element, geoFacade.Id, elementMap, "Vertex2", i, "WiresDatum")

                        vertexList.append(startPoint)
                        vertexList.append(endPoint)
                
                if type(geo.toShape()).__name__ == "Edge":
                    geoType = "Edge"

                    sketchIndexEdges += 1
                elif type(geo.toShape()).__name__ == "Vertex":
                    geoType = "Vertex"

                    sketchIndexVertices += 1
                                
                #Handle SketchProj
                
                geoShape = geo.toShape()
                #geoShape.Placement.Base = vector
                
                # implement hashes for vertices of lines and arcs
                if geoType == "Edge":
                    projElement = (obj.SketchProjection, geoType + str(sketchIndexEdges))

                    sketchIndexEdges += 1

                    element = (obj.SketchProjection, geoType + str(sketchIndexEdges))
                else:
                    projElement = (obj.SketchProjection, geoType + str(sketchIndexVertices))

                    sketchIndexVertices += 1

                    element = (obj.SketchProjection, geoType + str(sketchIndexVertices))
                
                print(projElement[1])
                print(element[1])
                print(geoFacade.Id)
                
                print("ProjElement: " + projElement[0].Label + "." + projElement[1])
                print("Element: " + element[0].Label + "." + element[1])

                newShape = geoShape.copy()
                newShape.Placement.Base = (newShape.Placement.Base + (sketch.Placement.Base + extrudeVector)) + offsetVector
                newShape.Placement.Rotation = sketch.Placement.Rotation

                print(sketch.Placement.Rotation)

                obj.SketchProjection.Shape = Part.Compound([obj.SketchProjection.Shape, newShape])

                newShape = geoShape.copy()
                newShape.Placement.Base = (newShape.Placement.Base + (sketch.Placement.Base)) + offsetVector
                newShape.Placement.Rotation = sketch.Placement.Rotation
                
                obj.SketchProjection.Shape = Part.Compound([obj.SketchProjection.Shape, newShape])

                elementMap = self.updateElement(projElement, geoFacade.Id, elementMap, geoType, 0, "SketchProj")
                elementMap = self.updateElement(element, geoFacade.Id, elementMap, geoType, 0, "Sketch")
            
            App.Console.PrintLog(obj.Label + " update datums time: " + str(time.time() - startTime) + "\n")
            
            for hash, value in elementMap.copy().items():
                if int(value["GeoId"]) not in idList:
                    elementMap.pop(hash)

            obj.ElementMap = json.dumps(elementMap)
            
            obj.WiresDatum.Placement = sketch.Placement
            obj.WiresDatum.Placement.Base += offsetVector

            obj.ViewObject.LineWidth = 1
            obj.WiresDatum.ViewObject.LineWidth = 2
            obj.Support.ViewObject.LineWidth = 2
            obj.SketchProjection.ViewObject.LineWidth = 2

            obj.Support.purgeTouched()
            obj.WiresDatum.purgeTouched()
            obj.SketchProjection.purgeTouched()
            
            obj.WiresDatum.Visibility = True
            obj.SketchProjection.Visibility = True
            obj.Support.Visibility = False

            return extrusion

    def execute(self, obj):
        if obj.Group == []:
            obj.Group = [obj.Support, obj.SketchProjection, obj.WiresDatum]

        self.updateProps(obj)
            
    def onChanged(self, obj, prop):
        if prop == "Length":
            obj.touch()

        super(Extrusion, self).onChanged(obj, prop)
            
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

class ViewProviderExtrusion:
    def __init__(self, obj):
        obj.Proxy = self
        obj.Selectable = False
        self.Origin = None
    
    def onDelete(self, vobj, subelements):
        if hasattr(vobj.Object, "WiresDatum"):
            if vobj.Object.WiresDatum != None:
                vobj.Object.Document.removeObject(vobj.Object.WiresDatum.Name)

        if hasattr(vobj.Object, "SketchProjection"):
            if vobj.Object.SketchProjection != None:
                vobj.Object.Document.removeObject(vobj.Object.SketchProjection.Name)
        
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
        if hasattr(self, "Object"):
            return [self.Object.Object.Support, self.Object.Object.WiresDatum, self.Object.Object.SketchProjection] 
        return []

    def dragObject(self, obj):
        App.Console.PrintMessage(obj)

    def __getstate__(self):
        # Called when saving
        return None

    def __setstate__(self, state):
        # Called when restoring
        return None
    
def makeExtrusion():
    activeObject = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")

    if activeObject != None and hasattr(activeObject, "Type") and activeObject.Type == "PartContainer":
        selectedObject = Gui.Selection.getSelection()
        doc = activeObject.Document
        doc.openTransaction("CreateExtrusion")

        if len(selectedObject) == 0:
            selectedObject = None
        else:
            selectedObject = selectedObject[0]

        if selectedObject != None and (selectedObject.TypeId == "Sketcher::SketchObject" or isType(selectedObject, "BoundarySketch")):
            obj = doc.addObject("Part::FeaturePython", "Extrusion")
            wiresDatum = doc.addObject("Part::Feature", "WiresDatum")
            wiresDatum.addProperty("App::PropertyString", "Type")
            wiresDatum.Type = "WiresDatum"

            sketchProjection = doc.addObject("Part::Feature", "SketchProjection")
            sketchProjection.addProperty("App::PropertyString", "Type")
            sketchProjection.Type = "SketchProjection"

            wiresDatum.ViewObject.ShowInTree = False
            sketchProjection.ViewObject.ShowInTree = False

            Extrusion(obj)
            ViewProviderExtrusion(obj.ViewObject)

            if len(selectedObject.InList) != 0:
                parent = selectedObject.InList[0]

                if hasattr(parent, "Type") and parent.Type == "PartContainer":
                    if hasattr(parent, "Group"):
                        group = parent.Group
                        if selectedObject in group:
                            group.remove(selectedObject)

                            parent.Group = group

            obj.Proxy.setSupport(obj, selectedObject)
            obj.Proxy.setDatums(obj, wiresDatum, sketchProjection)

            activeObject.Proxy.addObject(activeObject, obj, True)
            activeObject.Proxy.setTip(activeObject, obj)
        else:
            App.Console.PrintError("Selected object is not a sketch!\n")
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")
