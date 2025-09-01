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
from Utils import Utils
from Entities.Feature import Feature
from Utils import Constants
from Utils import GuiUtils
from Utils import SketchUtils
from PySide import QtWidgets
import copy

dimensionTypes = ["Blind", "UpToEntity"]
startingOffsetTypes = ["Blind", "UpToEntity"]

# 0 for linear, 1 for circular

class PatternTaskPanel:
    def __init__(self, obj):
        self.form = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout(self.form)
        self.layout.addWidget(QtWidgets.QLabel("Editing: " + obj.Label))
        self.extrusion = obj
        self.activeLayouts = []
        self.container = self.extrusion.Proxy.getContainer(self.extrusion)
        self.unitMult = None

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
        self.oldXCount = obj.XAxisCount if hasattr(obj, 'XAxisCount') else None
        self.oldYCount = obj.YAxisCount if hasattr(obj, 'YAxisCount') else None

        self.cancelButton.clicked.connect(self.reject)

        self.patternWidget = self.createBlindDimension()
        self.layout.addWidget(self.patternWidget)
    
    def createSOffsetUTE(self):
        return QtWidgets.QWidget()
    
    def createSOffsetBlind(self):
        return QtWidgets.QWidget()
    
    def createUTEDimension(self):
        return QtWidgets.QWidget()

    def createBlindDimension(self):
        if hasattr(self.extrusion.XAxisLength, 'getUserPreferred'):
            self.xUnitMult = self.extrusion.XAxisLength.getUserPreferred()[1]
            self.oldX = self.extrusion.XAxisLength.Value
        else:
            self.xUnitMult = 1
            self.oldX = self.extrusion.XAxisLength
        if hasattr(self.extrusion.YAxisLength, 'getUserPreferred'):
            self.yUnitMult = self.extrusion.YAxisLength.getUserPreferred()[1]
            self.oldY = self.extrusion.YAxisLength.Value
        else:
            self.yUnitMult = 1
            self.oldY = self.extrusion.YAxisLength

        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        xRow = QtWidgets.QHBoxLayout()
        xLabel = QtWidgets.QLabel("X Length:")
        self.xInput = QtWidgets.QDoubleSpinBox()
        self.xInput.setMinimum(-100000)
        self.xInput.setMaximum(100000)
        self.xInput.setSingleStep(1)
        xRow.setContentsMargins(10, 0, 0, 0)
        self.xInput.setValue(self.oldX / self.xUnitMult)
        xRow.addWidget(xLabel)
        xRow.addWidget(self.xInput)
        xRow.addStretch()

        yRow = QtWidgets.QHBoxLayout()
        yLabel = QtWidgets.QLabel("Y Length:")
        self.yInput = QtWidgets.QDoubleSpinBox()
        self.yInput.setMinimum(-100000)
        self.yInput.setMaximum(100000)
        self.yInput.setSingleStep(1)
        yRow.setContentsMargins(10, 0, 0, 0)
        self.yInput.setValue(self.oldY / self.yUnitMult)
        yRow.addWidget(yLabel)
        yRow.addWidget(self.yInput)
        yRow.addStretch()

        countsRow = QtWidgets.QHBoxLayout()
        xCountLabel = QtWidgets.QLabel("X Count:")
        self.xCountInput = QtWidgets.QSpinBox()
        self.xCountInput.setMinimum(1)
        self.xCountInput.setMaximum(100000)
        self.xCountInput.setValue(self.extrusion.XAxisCount)
        yCountLabel = QtWidgets.QLabel("Y Count:")
        self.yCountInput = QtWidgets.QSpinBox()
        self.yCountInput.setMinimum(1)
        self.yCountInput.setMaximum(100000)
        self.yCountInput.setValue(self.extrusion.YAxisCount)
        countsRow.addWidget(xCountLabel)
        countsRow.addWidget(self.xCountInput)
        countsRow.addWidget(yCountLabel)
        countsRow.addWidget(self.yCountInput)
        countsRow.addStretch()

        layout.addLayout(xRow)
        layout.addLayout(yRow)
        layout.addLayout(countsRow)
        widget.setLayout(layout)
        return widget
    
    def offsetTypeChanged(self, index):
        pass
    
    def dimensionTypeChanged(self, index):
        pass
    
    def updateGuiStartingOffset(self):
        pass
    
    def updateGuiDimensionType(self):
        pass

    def update(self):
        if hasattr(self.extrusion.XAxisLength, 'Value'):
            self.extrusion.XAxisLength.Value = (self.xInput.value() * self.xUnitMult)
        else:
            self.extrusion.XAxisLength = self.xInput.value()
        if hasattr(self.extrusion.YAxisLength, 'Value'):
            self.extrusion.YAxisLength.Value = (self.yInput.value() * self.yUnitMult)
        else:
            self.extrusion.YAxisLength = self.yInput.value()
        self.extrusion.XAxisCount = self.xCountInput.value()
        self.extrusion.YAxisCount = self.yCountInput.value()
        self.container.recompute()
    
    def accept(self):
        self.update()

        Gui.Control.closeDialog()

    def reject(self):
        if hasattr(self, "oldX"):
            if hasattr(self.extrusion.XAxisLength, 'Value'):
                self.extrusion.XAxisLength.Value = self.oldX
            else:
                self.extrusion.XAxisLength = self.oldX
        if hasattr(self, "oldY"):
            if hasattr(self.extrusion.YAxisLength, 'Value'):
                self.extrusion.YAxisLength.Value = self.oldY
            else:
                self.extrusion.YAxisLength = self.oldY
        self.container.recompute()

        Gui.Control.closeDialog()

    def getStandardButtons(self):
        return 0

    def getTitle(self):
        return "Extrusion Task Panel"

    def IsModal(self):
        return False

class Pattern(Feature):
    def __init__(self, obj):
        obj.Proxy = self
        self.updateProps(obj)
        
    def updateProps(self, obj, patternType=0):
        super(Pattern, self).updateProps(obj, hasRemove=False)

        if not hasattr(obj, "Boundary"):
            obj.addProperty("App::PropertyXLink", "Boundary", "ConstraintDesign")
            obj.setEditorMode("Boundary", 3)
        
        if not hasattr(obj, "Features"):
            obj.addProperty("App::PropertyLinkList", "Features", "ConstraintDesign")
        
        if not hasattr(obj, "PatternType"):
            obj.addProperty("App::PropertyInteger", "PatternType", "ConstraintDesign", "Pattern type.")
            obj.setEditorMode("PatternType", 3)
            obj.PatternType = patternType
        
        if patternType == 0:
            if not hasattr(obj, "XAxisCount"):
                obj.addProperty("App::PropertyInteger", "XAxisCount", "ConstraintDesign", "Number of features propogated along the X axis.")
                obj.XAxisCount = 2
            
            if (not hasattr(obj, "XAxisLength")
                or obj.getTypeIdOfProperty("XAxisLength") == "App::PropertyFloat"
                or obj.getTypeIdOfProperty("XAxisLength") == "App::PropertyLength"
            ):
                newVal = 10
                if hasattr(obj, "XAxisLength"):
                    if hasattr(obj.XAxisLength, "Value"):
                        newVal = obj.XAxisLength.Value
                    else:
                        newVal = obj.XAxisLength
                    obj.removeProperty("XAxisLength")
                obj.addProperty("App::PropertyDistance", "XAxisLength", "ConstraintDesign")
                obj.XAxisLength.Value = newVal
            
            if not hasattr(obj, "YAxisCount"):
                obj.addProperty("App::PropertyInteger", "YAxisCount", "ConstraintDesign", "Number of features propogated along the Y axis.")
                obj.YAxisCount = 2
            
            if (not hasattr(obj, "YAxisLength")
                or obj.getTypeIdOfProperty("YAxisLength") == "App::PropertyFloat"
                or obj.getTypeIdOfProperty("YAxisLength") == "App::PropertyLength"
            ):
                newVal = 10
                if hasattr(obj, "YAxisLength"):
                    if hasattr(obj.YAxisLength, "Value"):
                        newVal = obj.YAxisLength.Value
                    else:
                        newVal = obj.YAxisLength
                    obj.removeProperty("YAxisLength")
                obj.addProperty("App::PropertyDistance", "YAxisLength", "ConstraintDesign")
                obj.YAxisLength.Value = newVal

            if not hasattr(obj, "DirectionPlane"):
                obj.addProperty("App::PropertyStringList", "DirectionPlane", "ConstraintDesign")
            
            if hasattr(obj, "DirectionLine"):
                obj.DirectionPlane = [obj.DirectionLine]
                obj.removeProperty("DirectionLine")
        
        if not hasattr(obj, "Support"):
            obj.addProperty("App::PropertyXLink", "Support", "ConstraintDesign", "Support object (ex: A sketch)")
        
        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")

            if obj.PatternType == 0:
                obj.Type = "LinearPattern"
            elif obj.PatternType == 1:
                obj.Type = "CircularPattern"

        if not hasattr(obj, "SkipMerge"):
            obj.addProperty("App::PropertyBool", "SkipMerge", "ConstraintDesign", "Determines whether to perform boolean operations on the previous shape or not.")
            obj.SkipMerge = False
        
        if not hasattr(obj, "Group"):
            obj.addProperty("App::PropertyLinkList", "Group", "ConstraintDesign", "Group")
        
    def showGui(self, obj):
        Gui.Control.showDialog(PatternTaskPanel(obj))

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
        
    def setSupport(self, obj, support):
        obj.Support = support

        self.addObject(obj, support)
    
    def getContainer(self, obj):
        return super(Pattern, self).getContainer(obj)

    # Format {"HashName": {"Element:" edge, "GeoId", "ElType": Vertex/Edge, sketchGeoId, "Occurrence": 0-∞, "FeatureType": Sketch, SketchProj, WiresDatum}}
    # def updateElement(self, element, id, map, elType, occurrence = 0, featureType = "Sketch"):
        # hasElement = False

        # for key, value in map.items():
        #     if value["GeoId"] == id and value["Occurrence"] == occurrence and ((value.get("ElType") == None and value["Element"].split(".")[1].startswith(element[1])) or (value.get("ElType") != None and value["ElType"] == elType)) and value["FeatureType"] == featureType:
        #         map[key]["Element"] = str(element[0].Name) + "." + str(element[1])
        #         map[key]["ElType"] = elType

        #         hasElement = True

        # if hasElement == False:
        #     hash = Utils.generateHashName(map)
            
        #     map[hash] = {"Element": str(element[0].Name) + "." + str(element[1]), "GeoId": id, "Occurrence": occurrence, "FeatureType": featureType, "ElType": elType}
        
        # return map
    
    def generateShape(self, obj, prevShape):
        self.updateProps(obj)
        finalShape = prevShape.copy()
        individualShape = Part.Shape()
        finalIndividualShape = Part.Shape()
        baseBoundarySh, initialMap = Utils.makeBoundaryCompound(obj.Features, True, obj.Boundary.Name)
        finalMap = {}
        boundaryCompound = Part.Shape()
        occurence = 0 # necessary because of X and Y instances
        numEdges = len(baseBoundarySh.Edges)
        numVertexes = len(baseBoundarySh.Vertexes)
        addShape = Part.Shape()
        removeShape = Part.Shape()
        finalAddArray = []
        finalRemoveArray = []

        for feature in obj.Features:
            featureShapes = feature.Proxy.getIndividualShapes(feature)

            for _, v in featureShapes.items():
                featureShape = v["Shape"].copy()
                remove = v["Remove"]

                if remove:
                    removeShape = Part.Compound([removeShape, featureShape])
                else:
                    addShape = Part.Compound([addShape, featureShape])

                if individualShape.isNull():
                    individualShape = featureShape
                else:
                    if remove:
                        individualShape = individualShape.cut(featureShape)
                    else:
                        individualShape = individualShape.fuse(featureShape)
        

        if obj.PatternType == 0:
            rot = App.Rotation()

            if len(obj.DirectionPlane) != 0:
                container = self.getContainer(obj)
                plane = Utils.getPlaneFromStringIDList(container, obj.DirectionPlane, requestingObjectLabel = obj.Label)

                if plane != None:
                    rot = plane.Rotation
            
            placementLocations = []
            
            for Yi in range(obj.YAxisCount):
                y = Yi * (obj.YAxisLength.Value if hasattr(obj.YAxisLength, 'Value') else obj.YAxisLength)

                for Xi in range(obj.XAxisCount):
                    x = Xi * (obj.XAxisLength.Value if hasattr(obj.XAxisLength, 'Value') else obj.XAxisLength)

                    if x == 0 and y == 0:
                        continue

                    placementLocations.append(rot.multVec(App.Vector(x, y, 0)))

            for location in placementLocations:
                newBoundary = baseBoundarySh.copy()
                newBoundary.Placement.Base = location
                boundaryCompound = Part.Compound([boundaryCompound, newBoundary])

                newAddShape = addShape.copy()
                newAddShape.Placement.Base = location

                newRemoveShape = removeShape.copy()
                newRemoveShape.Placement.Base = location

                if not newAddShape.isNull():
                    finalAddArray.append(newAddShape)
                if not newRemoveShape.isNull():
                    finalRemoveArray.append(newRemoveShape)


                # newIndividualShape = individualShape.copy()
                # newIndividualShape.Placement.Base = location
                # finalIndividualShape = Part.Compound([finalIndividualShape, newIndividualShape])
                    
                for k,v in initialMap.items():
                    newKey = f"{k}:;{str(occurence)}"
                    elementNumber = 0
                    elementSplit = v["Element"].split(".")
                    element = elementSplit[1]
                    newElement = v["Element"] # set to old element as a backup

                    if element.startswith("Edge"):
                        elementNumber = int(element.removeprefix("Edge"))
                        elementNumber += (numEdges * occurence)

                        newElement = f"{elementSplit[0]}.Edge{elementNumber}"
                    elif element.startswith("Vertex"):
                        elementNumber = int(element.removeprefix("Vertex"))
                        elementNumber += (numVertexes * occurence)

                        newElement = f"{elementSplit[0]}.Vertex{elementNumber}"
                    
                    finalMap[newKey] = copy.copy(v)
                    finalMap[newKey]["Element"] = copy.copy(newElement)
                
                occurence += 1
        
        obj.IndividualShape = finalIndividualShape.copy()

        if not obj.SkipMerge:
            if len(finalAddArray) != 0:
                finalShape = finalShape.fuse(Part.Compound(finalAddArray))
            
            if len(finalRemoveArray) != 0:
                finalShape = finalShape.cut(Part.Compound(finalRemoveArray))
        
        obj.Shape = finalShape
        obj.Boundary.Shape = boundaryCompound
        obj.Boundary.ViewObject.LineWidth = Constants.boundaryLineWidth
        obj.Boundary.ViewObject.PointSize = Constants.boundaryPointSize

        obj.Boundary.purgeTouched()

        try:
            finalStringMap = json.dumps(finalMap)
        except:
            finalStringMap = "{}"

            App.Console.PrintError("Unable to stringify elementMap!")
        
        obj.ElementMap = finalStringMap

        return finalShape

    def execute(self, obj):
        self.updateProps(obj)
            
    def onChanged(self, obj, prop):
        super(Pattern, self).onChanged(obj, prop)
            
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None

class ViewProviderPattern:
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
        # vobj.Object.Document.openTransaction("EditPattern")
        # vobj.Object.Proxy.showGui(vobj.Object)

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
        if self.Object != None and self.Object.Object != None and self.Object.Object.PatternType == 0:
            return os.path.join(os.path.dirname(__file__), "..", "icons", "LinearPattern.svg")
    
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
    
def makePattern(patternType):
    activeObject = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")

    if Utils.isType(activeObject, "PartContainer"):
        selectedObjects = Gui.Selection.getSelection()
        doc = activeObject.Document
        doc.openTransaction("CreatePattern")

        if len(selectedObjects) != 0:
            obj = doc.addObject("Part::FeaturePython", "Pattern")
            boundary = doc.addObject("Part::Feature", "Boundary")
            boundary.addProperty("App::PropertyString", "Type")
            boundary.Type = "Boundary"

            Pattern(obj)
            ViewProviderPattern(obj.ViewObject)

            obj.Proxy.setBoundary(obj, boundary)
            obj.Features = selectedObjects

            activeObject.Proxy.addObject(activeObject, obj, True)
            activeObject.Proxy.setTip(activeObject, obj)
        else:
            App.Console.PrintError("Selected object is not a sketch!\n")
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")
