import FreeCAD as App
import FreeCADGui as Gui
import Part
import sys
import os
import json
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from Utils.Utils import isType, getDistanceToElement, generateHashName
from Utils.SketchUtils import getIDDict
from Utils.Constants import *
from Entities.Feature import Feature
from PySide import QtWidgets
from Utils.GuiUtils import SelectorWidget

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

        self.selectorWidget.cleanup()
        self.sOffsetSelectorWidget.cleanup()

        Gui.Control.closeDialog()

    def reject(self):
        if hasattr(self, "oldLength"):
            self.extrusion.Length = self.oldLength
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

class Extrusion(Feature):
    def __init__(self, obj):
        obj.Proxy = self
        self.updateProps(obj)
        
    def updateProps(self, obj):
        super(Extrusion, self).updateProps(obj)

        if not hasattr(obj, "Boundary"):
            obj.addProperty("App::PropertyXLink", "Boundary", "ConstraintDesign")
            obj.setEditorMode("Boundary", 3)
        
        if not hasattr(obj, "Support"):
            obj.addProperty("App::PropertyXLink", "Support", "ConstraintDesign", "Support object (ex: A sketch)")
        
        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "Extrusion"

        if not hasattr(obj, "DimensionType"):
            obj.addProperty("App::PropertyEnumeration", "DimensionType", "ConstraintDesign", "Determines the type of dimension that controls the length of extrusion.")
            obj.DimensionType = dimensionTypes
            obj.DimensionType = "Blind"

        if not hasattr(obj, "Symmetric"):
            obj.addProperty("App::PropertyBool", "Symmetric", "ConstraintDesign", "Determines if this extrusion will be symmetric to the extrusion plane.")
            obj.Symmetric = False
        
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
    
    def showGui(self, obj):
        Gui.Control.showDialog(ExtrusionTaskPanel(obj))

    def setBoundary(self, obj, boundary):
        obj.Boundary = boundary

        self.addObject(obj, boundary)
    
    def getSupports(self, obj):
        if hasattr(obj, "Support") and obj.Support != None:
            return [obj.Support]
        else:
            return []
    
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
        
    def setSupport(self, obj, support):
        obj.Support = support

        self.addObject(obj, support)
    
    def getContainer(self, obj):
        return super(Extrusion, self).getContainer(obj)

    def makeIdentifier(self, geoIDs = ["g1v1", "g2"], elementType = "Edge", occurence = 0, boundaryType = "Sketch", extraInfo=""):
        geoIDString = ":".join(geoIDs)

        if not extraInfo.endswith(";"): extraInfo += ";"

        return f"{geoIDString};{elementType};{str(occurence)};{boundaryType};;;{extraInfo}"
    
    def identifierIsSame(self, identifier1, identifier2):
        identifier1Array = identifier1.split(";")
        identifier2Array = identifier2.split(";")
        identifier1GeoIDs = identifier1Array[0].split(":")
        identifier2GeoIDs = identifier2Array[0].split(":")

        if (identifier1 == identifier2) or ((identifier1Array[1:] == identifier2Array[1:]) and len(set(identifier1GeoIDs) & set(identifier2GeoIDs)) >= 1):
            return True
        else:
            return False

    # Format {"HashName": {"Element:" edge, "Stale": <True/False>, "Identifier": "g1:g2v2;<ElType>;<Occurence>;<BoundaryType -> (Sketch/SketchProjection/WiresBoundary)>;;;<extraInfo>"}}
    def updateElement(self, element, identifier, map, complexCheck=True):
        hasElement = False

        for key, value in map.items():
            if (not complexCheck and value["Identifier"] == identifier) or (complexCheck and self.identifierIsSame(value["Identifier"], identifier)):
                map[key]["Identifier"] = identifier
                map[key]["Element"] = str(element[0].Name) + "." + str(element[1])
                map[key]["Stale"] = False

                hasElement = True

        if hasElement == False:
            hash = generateHashName(map)
            
            map[hash] = {"Element": str(element[0].Name) + "." + str(element[1]), "Stale": False, "Identifier": identifier}
        
        return map
    
    def generateShape(self, obj, prevShape):
        self.updateProps(obj)

        if hasattr(obj,"Support") and isType(obj.Support, "BoundarySketch"):
            sketch = obj.Support
            container = self.getContainer(obj)

            sketch.Proxy.updateSketch(sketch, container)
            sketchWires = list(filter(lambda w: w.isClosed(), sketch.Shape.Wires))
            face = Part.makeFace(sketchWires)
            ZOffset = 0
            normal = sketch.Placement.Rotation.multVec(App.Vector(0, 0, 1))
            extrudeLength = 1

            if obj.DimensionType == "Blind":
                extrudeLength = obj.Length

            if obj.Symmetric:
                if not obj.StartingOffset:
                    ZOffset += -extrudeLength / 2
                else:
                    App.Console.PrintWarning(f"({obj.Label}) Cannot enable symmetry and starting offset in one extrusion!\n")
                        
            if obj.StartingOffset:
                if obj.StartingOffsetType == "Blind":
                    ZOffset += obj.StartingOffsetLength
                elif obj.StartingOffsetType == "UpToEntity" and obj.StartingOffsetUpToEntity != "":
                    ZOffset += getDistanceToElement(obj, obj.StartingOffsetUpToEntity, sketch.Placement.Base, normal, requestingObjectLabel=obj.Label)
            
            offsetVector = normal * ZOffset       

            if obj.DimensionType == "UpToEntity" and obj.UpToEntity != "":
                extrudeLength = getDistanceToElement(obj, obj.UpToEntity, (sketch.Placement.Base + offsetVector), normal, requestingObjectLabel=obj.Label)

            extrudeVector = normal * extrudeLength

            if extrudeLength != 0:
                extrusion = face.extrude(extrudeVector)

                obj.IndividualShape = extrusion.copy()

                if not prevShape.isNull():
                    if obj.Remove:
                        extrusion = prevShape.cut(extrusion)
                    else:
                        extrusion = prevShape.fuse(extrusion)
            else:
                obj.IndividualShape = Part.Shape()
                extrusion = prevShape

            extrusion.Placement.Base = extrusion.Placement.Base + offsetVector
            obj.Shape = extrusion
        
            if not hasattr(obj, "ElementMap"):
                try:
                    self.updateProps(obj)
                except Exception as e:
                    raise Exception("Unable to create ElementMap property! Error: " + str(e))
            
            try:
                elementMap = json.loads(obj.ElementMap)
            except:
                raise Exception("The Element Map is an invalid json string!")
            
            identifierList = []

            # 0: {"Vector": App.Vector(), "IDs": ["g1v1", "g3v2"]}
            points = {}
            # "ElementName": {"Vector": App.Vector(), "Type": "<Sketch/SketchProjection>"}
            unsupportedVertexes = {} # i want to check if vertexes have already been generated, so they can be supported properly later

            startTime = time.time()
            boundaryShape = Part.Shape()
            tol = 1e-5
            facadeDict = getIDDict(sketch)

            for id, geo in facadeDict.items():
                if hasattr(geo, "StartPoint") and hasattr(geo, "EndPoint"):
                    vertexes = [geo.StartPoint, geo.EndPoint]

                    for i,vec in enumerate(vertexes):
                        hasVector = False

                        for _,v in points.items():
                            if v["Vector"].isEqual(vec, tol):
                                hasVector = True

                                v["IDs"].append(f"{id}v{str(i + 1)}")
                    
                        if not hasVector:
                            points[len(points)] = {"Vector": vec, "IDs": [f"{id}v{str(i + 1)}"]}
                elif hasattr(geo, "X") and hasattr(geo, "Y") and hasattr(geo, "Z"):
                    vec = App.Vector(geo.X, geo.Y, geo.Z)
                    hasVector = False

                    for _,v in points.items():
                        if v["Vector"].isEqual(vec, tol):
                            hasVector = True

                            v["IDs"].append(f"{id}")
        
                    if not hasVector:
                        points[len(points)] = {"Vector": vec, "IDs": [f"{id}"]}
                
                geoShape = geo.toShape()
                oldVertNum = len(boundaryShape.Vertexes)
                boundaryShape = Part.Compound([boundaryShape, geoShape])
                newVertNum = len(boundaryShape.Vertexes)
                newVertexList = boundaryShape.Vertexes[oldVertNum:newVertNum]

                for i, vec in enumerate(newVertexList):
                    unsupportedVertexes[f"Vertex{str((i + 1) + oldVertNum)}"] = {"Vector": vec.Point, "Type": "Sketch"}

                if isinstance(geoShape, Part.Edge):
                    # Create Base Sketch Boundary
                    identifier = self.makeIdentifier([f"{id}"], "Edge", 0, "Sketch")
                    identifierList.append(identifier)
                    element = (obj.Boundary, f"Edge{str(len(boundaryShape.Edges))}")
                    
                    self.updateElement(element, identifier, elementMap, False)
                
                if extrudeLength != 0:
                    geoShape = geo.toShape()
                    geoShape.Placement.Base += App.Vector(0, 0, extrudeLength)
                    oldVertNum = len(boundaryShape.Vertexes)
                    boundaryShape = Part.Compound([boundaryShape, geoShape])
                    newVertNum = len(boundaryShape.Vertexes)
                    newVertexList = boundaryShape.Vertexes[oldVertNum:newVertNum]

                    for i, vec in enumerate(newVertexList):
                        unsupportedVertexes[f"Vertex{str((i + 1) + oldVertNum)}"] = {"Vector": (vec.Point - extrudeVector), "Type": "SketchProjection"}

                    if isinstance(geoShape, Part.Edge):
                        # Create Base Sketch Boundary
                        identifier = self.makeIdentifier([f"{id}"], "Edge", 0, "SketchProjection")
                        identifierList.append(identifier)
                        element = (obj.Boundary, f"Edge{str(len(boundaryShape.Edges))}")
                        
                        self.updateElement(element, identifier, elementMap, False)

            App.Console.PrintLog(f"{obj.Label} create points time: {str(time.time() - startTime)}\n")

            geoIDs = []

            # Generate WiresBoundary and map Vertexes appended by the prior loop
            for _,v in points.items():
                # Start with edges
                if extrudeLength != 0:
                    startPoint = v["Vector"]
                    endPoint = v["Vector"] + App.Vector(0, 0, extrudeLength)
                    
                    line = Part.LineSegment(startPoint, endPoint).toShape()
                    oldVertNum = len(boundaryShape.Vertexes)
                    boundaryShape = Part.Compound([boundaryShape, line])
                    newVertNum = len(boundaryShape.Vertexes)

                    newVertexes = boundaryShape.Vertexes[oldVertNum:newVertNum]
                    startVertex = None
                    endVertex = None

                    if newVertexes[0].Point.isEqual(startPoint, tol):
                        startVertex = f"Vertex{str(oldVertNum+1)}"
                        endVertex = f"Vertex{str(oldVertNum+2)}"
                    elif newVertexes[1].Point.isEqual(startPoint, tol):
                        startVertex = f"Vertex{str(oldVertNum+2)}"
                        endVertex = f"Vertex{str(oldVertNum+1)}"
                    
                    # Handle start vertex
                    identifier = self.makeIdentifier(v["IDs"], "Vertex", 0, "WiresBoundary", "BottomPoint")
                    identifierList.append(identifier)
                    element = (obj.Boundary, startVertex)
                    self.updateElement(element, identifier, elementMap)

                    # Handle end vertex
                    identifier = self.makeIdentifier(v["IDs"], "Vertex", 0, "WiresBoundary", "TopPoint")
                    identifierList.append(identifier)
                    element = (obj.Boundary, endVertex)
                    self.updateElement(element, identifier, elementMap)

                    # Handle wire boundary
                    identifier = self.makeIdentifier(v["IDs"], "Edge", 0, "WiresBoundary")
                    identifierList.append(identifier)
                    element = (obj.Boundary, f"Edge{str(len(boundaryShape.Edges))}")
                    self.updateElement(element, identifier, elementMap)

                # Handle old loop vertexes
                for elementName, uV in unsupportedVertexes.items():
                    if v["Vector"].isEqual(uV["Vector"], tol):
                        identifier = self.makeIdentifier(v["IDs"], "Vertex", geoIDs.count(v["IDs"]), uV["Type"])
                        identifierList.append(identifier)
                        element = (obj.Boundary, elementName)
                        self.updateElement(element, identifier, elementMap)

                        geoIDs.append(v["IDs"])
            
            for hash, value in elementMap.copy().items():
                if value["Identifier"] not in identifierList:
                    # elementMap.pop(hash)
                    elementMap[hash]["Stale"] = True

            App.Console.PrintLog(f"{obj.Label} total datum time: {str(time.time() - startTime)}\n")

            obj.ElementMap = json.dumps(elementMap)
            
            obj.Boundary.Shape = boundaryShape
            obj.Boundary.ViewObject.LineWidth = boundaryLineWidth
            obj.Boundary.ViewObject.PointSize = boundaryPointSize
            obj.Boundary.Placement = sketch.Placement
            obj.Boundary.Placement.Base += offsetVector

            obj.Support.purgeTouched()
            obj.Boundary.purgeTouched()

            obj.Boundary.Visibility = True
            obj.Support.Visibility = False

            return extrusion

    def execute(self, obj):
        if obj.Group == []:
            obj.Group = [obj.Support, obj.Boundary]

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
        if hasattr(vobj.Object, "Boundary") and vobj.Object.Boundary != None:
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
        if hasattr(self, "Object"):
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
            boundary = doc.addObject("Part::Feature", "Boundary")
            boundary.addProperty("App::PropertyString", "Type")
            boundary.Type = "Boundary"

            boundary.ViewObject.ShowInTree = True

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
            obj.Proxy.setBoundary(obj, boundary)

            activeObject.Proxy.addObject(activeObject, obj, True)
            activeObject.Proxy.setTip(activeObject, obj)

            # obj.Proxy.showGui(obj)
        else:
            App.Console.PrintError("Selected object is not a sketch!\n")
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")
