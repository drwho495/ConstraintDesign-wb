import FreeCAD as App
import FreeCADGui as Gui
import Part
import sys
import os
import re
import json
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from Utils import Utils
from Utils import SketchUtils
from Utils import Constants
from Entities.Feature import Feature
from PySide import QtWidgets
from Utils import GuiUtils
from Utils import GeometryUtils
from typing import List

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
        self.unitMult = self.extrusion.Length.getUserPreferred()[1]

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
        self.oldStartingOffsetLength = obj.StartingOffsetLength.Value
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
        widget = GuiUtils.SelectorWidget(container=self.container, startSelection=[self.extrusion.StartingOffsetUpToEntity], sizeLimit=1)
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
        self.sOffsetBlindInput.setValue((self.oldStartingOffsetLength / self.unitMult))

        self.sOffestBlindLayout.addWidget(self.sOffsetBlindLabel)
        self.sOffestBlindLayout.addWidget(self.sOffsetBlindInput)
        self.sOffestBlindWidget.setLayout(self.sOffestBlindLayout)

        return self.sOffestBlindWidget
    
    def createUTEDimension(self):
        widget = GuiUtils.SelectorWidget(container=self.container, startSelection=[self.extrusion.UpToEntity], sizeLimit=1)
        return widget

    def createBlindDimension(self):
        self.oldLength = self.extrusion.Length.Value

        widget = QtWidgets.QWidget()
        self.blindDimensionRow = QtWidgets.QHBoxLayout()
        self.blindLabel = QtWidgets.QLabel("Length:")
        self.blindInput = QtWidgets.QDoubleSpinBox()
        self.blindInput.setMinimum(-100000)
        self.blindInput.setMaximum(100000)
        self.blindInput.setSingleStep(1)
        self.blindDimensionRow.setContentsMargins(10, 0, 0, 0)
        self.blindInput.setValue((self.oldLength / self.unitMult))

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
            self.extrusion.Length.Value = (self.blindInput.value() * self.unitMult)
        elif self.extrusion.DimensionType == "UpToEntity":
            selection = self.selectorWidget.getSelection()

            if len(selection) != 0:
                self.extrusion.UpToEntity = selection[0]
        
        if self.extrusion.StartingOffset:
            if self.extrusion.StartingOffsetType == "Blind":
                self.extrusion.StartingOffsetLength.Value = (self.sOffsetBlindInput.value() * self.unitMult)
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
        self.extrusion.StartingOffsetLength.Value = self.oldStartingOffsetLength
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
        self.timeTakeUE = 0
    
    def attach(self, obj):
        self.timeTakeUE = 0
        
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
        
        if not hasattr(obj, "IncludeConstruction"):
            obj.addProperty("App::PropertyBool", "IncludeConstruction", "ConstraintDesign", "Tells the boundary generator to include construction geometry.")
            obj.IncludeConstruction = False
        
        if not hasattr(obj, "MakeIntersectionGeometry"):
            obj.addProperty("App::PropertyBool", "MakeIntersectionGeometry", "ConstraintDesign", "Determines if boundaries should include edges projected onto faces.")
            obj.MakeIntersectionGeometry = False
        
        if not hasattr(obj, "Group"):
            obj.addProperty("App::PropertyLinkList", "Group", "ConstraintDesign", "Group")
        
        if (not hasattr(obj, "Length")
            or obj.getTypeIdOfProperty("Length") == "App::PropertyFloat"
        ):
            newLength = 10

            if hasattr(obj, "Length"):
                if hasattr(obj.Length, "Value"):
                    newLength = obj.Length.Value
                else:
                    newLength = obj.Length

                obj.removeProperty("Length")

            obj.addProperty("App::PropertyDistance", "Length", "ConstraintDesign", "Length of extrusion.")
            obj.Length.Value = newLength
            
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
        
        if (not hasattr(obj, "StartingOffsetLength")
            or obj.getTypeIdOfProperty("StartingOffsetLength") == "App::PropertyFloat"
            or obj.getTypeIdOfProperty("StartingOffsetLength") == "App::PropertyLength"
        ):
            newStartingOffset = 0
            if hasattr(obj, "StartingOffsetLength"):
                if hasattr(obj.StartingOffsetLength, "Value"):
                    newStartingOffset = obj.StartingOffsetLength.Value
                else:
                    newStartingOffset = obj.StartingOffsetLength
                obj.removeProperty("StartingOffsetLength")
            obj.addProperty("App::PropertyDistance", "StartingOffsetLength", "ConstraintDesign")
            obj.StartingOffsetLength.Value = newStartingOffset
    
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

    def makeIdentifier(self, 
                       geoIDs: List[str] = [],
                       elementType: str = "Edge",
                       occurence: int = 0,
                       boundaryType: str = "Sketch",
                       boundaryExtraIDs: List[str] = [],
                       extraInfo: str = ""
    ) -> str:
        geoIDString = ":".join(geoIDs)
        boundaryExtraIDsStr = ""

        if len(boundaryExtraIDs) != 0:
            boundaryExtraIDsStr = f"({'|'.join(boundaryExtraIDs)})"

        if not extraInfo.endswith(";") and len(extraInfo) != 0: extraInfo += ";"

        return f"{geoIDString};{elementType};{str(occurence)};{boundaryType}{boundaryExtraIDsStr};;;{extraInfo}"
    
    def identifierIsSame(self, identifier1, identifier2, complexCheck = True):
        identifier1Array = re.split((r"{}(?![^()]*\))".format(re.escape(";"))), identifier1)
        identifier2Array = re.split((r"{}(?![^()]*\))".format(re.escape(";"))), identifier2)
        identifier1GeoIDs = identifier1Array[0].split(":")
        identifier2GeoIDs = identifier2Array[0].split(":")

        def makeOtherList(identifier, filterList):
            retList = []

            for section in identifier:
                if section == "": continue
                
                if filterList:
                    retList.append(re.sub(r'\(.*?\)', '', section))
                else:
                    retList.append(section)
            
            return retList[1:]

        identifier1OthersFiltered = makeOtherList(identifier1Array, True)
        identifier1Others = makeOtherList(identifier1Array, False)

        identifier2OthersFiltered = makeOtherList(identifier2Array, True)
        identifier2Others = makeOtherList(identifier2Array, False)

        if (identifier1Others[2].endswith(")") and identifier2Others[2].endswith(")")):
            internalGeoIDs1Matches = re.findall(r"\((.*?)\)", identifier1Others[2]) # type: ignore
            internalGeoIDs2Matches = re.findall(r"\((.*?)\)", identifier2Others[2]) # type: ignore

            if len(internalGeoIDs1Matches) == 1 and len(internalGeoIDs2Matches) == 1:
                internalGeoIDs1 = internalGeoIDs1Matches[0].split("|")
                internalGeoIDs2 = internalGeoIDs2Matches[0].split("|")

                if (len(internalGeoIDs1) != 0 and len(internalGeoIDs2) != 0) and (len(set(internalGeoIDs1) & set(internalGeoIDs2)) < 2):
                    return False
            else:
                return False

        if ((identifier1 == identifier2) 
            or ((identifier1OthersFiltered == identifier2OthersFiltered) 
                and ((not complexCheck and identifier1GeoIDs == identifier2GeoIDs) 
                     or (complexCheck 
                         and (identifier1Array[1:4] == identifier2Array[1:4]) and len(set(identifier1GeoIDs) & set(identifier2GeoIDs)) >= 1 or identifier1GeoIDs == identifier2GeoIDs)))):
            return True
        else:
            return False

    # Format {"HashName": {"Element:" edge, "Stale": <True/False>, "Identifier": "g1:g2v2;<ElType>;<Occurence>;<BoundaryType -> (Sketch/SketchProjection/Intersection/WiresBoundary)>;;;<extraInfo>"}}
    def updateElement(self, element, identifier, map, complexCheck = True):
        startTime = time.time()

        hasElement = False

        for key, value in map.items():
            if self.identifierIsSame(value["Identifier"], identifier, complexCheck):
                map[key]["Identifier"] = identifier
                map[key]["Element"] = str(element[0].Name) + "." + str(element[1])
                map[key]["Stale"] = False

                hasElement = True
                break

        if hasElement == False:
            hash = Utils.generateHashName(map)
            
            map[hash] = {"Element": str(element[0].Name) + "." + str(element[1]), "Stale": False, "Identifier": identifier}
        
        self.timeTakeUE += time.time() - startTime
        
        return map
    
    def generateShape(self, obj, prevShape):
        self.timeTakeUE = 0
        self.updateProps(obj)

        if hasattr(obj,"Support") and Utils.isType(obj.Support, Constants.supportTypes):
            sketch = obj.Support
            container = self.getContainer(obj)

            if Utils.isType(sketch, "BoundarySketch"):
                sketch.Proxy.updateSketch(sketch, container)
                
            sketchWires = list(filter(lambda w: w.isClosed(), sketch.Shape.Wires))
            face = Part.Face()
            
            if obj.Length.Value != 0:
                face = Part.makeFace(sketchWires) # type: ignore
                face.ElementMap = {}

            ZOffset = 0
            normal = sketch.Placement.Rotation.multVec(App.Vector(0, 0, 1))
            extrudeLength = 1

            if obj.DimensionType == "Blind":
                extrudeLength = obj.Length.Value

            if obj.Symmetric:
                if not obj.StartingOffset:
                    ZOffset += -extrudeLength / 2
                else:
                    App.Console.PrintWarning(f"({obj.Label}) Cannot enable symmetry and starting offset in one extrusion!\n")
                        
            if obj.StartingOffset:
                if obj.StartingOffsetType == "Blind":
                    ZOffset += obj.StartingOffsetLength.Value
                elif obj.StartingOffsetType == "UpToEntity" and obj.StartingOffsetUpToEntity != "":
                    ZOffset += Utils.getDistanceToElement(obj, obj.StartingOffsetUpToEntity, sketch.Placement.Base, normal, requestingObjectLabel=obj.Label)
            
            offsetVector = normal * ZOffset       

            if obj.DimensionType == "UpToEntity" and obj.UpToEntity != "":
                extrudeLength = Utils.getDistanceToElement(obj, obj.UpToEntity, (sketch.Placement.Base + offsetVector), normal, requestingObjectLabel=obj.Label)

            extrudeVector = normal * extrudeLength
            extrusion = prevShape
            intersectingFaceMap = {}
            basePoint = App.Placement()
            endExtrudePoint = App.Placement()

            basePoint = sketch.Placement.copy()
            basePoint.Base += offsetVector

            endExtrudePoint = basePoint.copy()
            endExtrudePoint.Base += extrudeVector

            if extrudeLength != 0:
                extrusion = face.extrude(extrudeVector)
                extrusion.Placement.Base += offsetVector

                obj.IndividualShape = extrusion.copy()
                if obj.MakeIntersectionGeometry:
                    filteredFeatures = []
                    features = container.Proxy.getGroup(container, False, True)
                    featureCompoundList = []

                    for item in features:
                        if item.Name != obj.Name and hasattr(item, "Shape"):
                            filteredFeatures.append(item)
                            featureCompoundList.append(item.Shape)
                        else:
                            break
                    
                    boundaryCompound, compElMap = Utils.makeBoundaryCompound(filteredFeatures, True, "_")
                    intersectingFaceMap = GeometryUtils.getIntersectingFaces(prevShape,
                                                               extrusion,
                                                               boundaryCompound,
                                                               compElMap)

                if not prevShape.isNull():
                    if obj.Remove:
                        extrusion = prevShape.cut(extrusion)
                    else:
                        extrusion = prevShape.fuse(extrusion)
            else:
                obj.IndividualShape = Part.Shape()

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
            boundaryElementsList = []
            boundaryEdgesList = []
            boundaryVertexesList = []
            tol = 1e-3
            facadeDict = SketchUtils.getIDDict(sketch, includeConstruction = obj.IncludeConstruction)

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
                geoShape.Placement = basePoint
                geoShape.Orientation = "Forward"
                oldVertNum = len(boundaryVertexesList)

                Utils.addElementToCompoundArray(geoShape, boundaryElementsList, boundaryEdgesList, boundaryVertexesList)

                newVertNum = len(boundaryVertexesList)
                newVertexList = boundaryVertexesList[oldVertNum:newVertNum]

                for i, vec in enumerate(newVertexList):
                    point = basePoint.inverse().multVec(vec.Point)
                    
                    unsupportedVertexes[f"Vertex{str((i + 1) + oldVertNum)}"] = {"Vector": point, "Type": "Sketch"}

                if isinstance(geoShape, Part.Edge):
                    # Create Base Sketch Boundary
                    identifier = self.makeIdentifier([f"{id}"], "Edge", 0, "Sketch")
                    identifierList.append(identifier)
                    element = (obj.Boundary, f"Edge{str(len(boundaryEdgesList))}")
                    
                    self.updateElement(element, identifier, elementMap)
                
                if extrudeLength != 0:
                    occurence = 0
                    intersectFaceTol = 1e-2
                    checkVertexes = []

                    for _, val in intersectingFaceMap.items():
                        faceIdentifier = val["Identifier"].split("|")
                        faceShape = val["Shape"]
                        try:
                            projGeoShape = faceShape.makeParallelProjection(geoShape, normal)
                            duplicate = False
                            
                            for edge in projGeoShape.Edges:
                                checkKey = []

                                for vert in edge.Vertexes:
                                    checkKey.append(vert.Point)

                                if checkKey in checkVertexes:
                                    duplicate = True
                                    break
                                else:
                                    checkVertexes.append(checkKey)
                            
                            if duplicate:
                                continue
                        except:
                            continue

                        startDist = Utils.getP2PDistanceAlongNormal(basePoint.Base, faceShape.CenterOfMass, normal)
                        endDist = Utils.getP2PDistanceAlongNormal(endExtrudePoint.Base, faceShape.CenterOfMass, normal)

                        if faceShape.Surface.TypeId == "Part::GeomPlane" and abs(startDist) < intersectFaceTol or abs(endDist) < intersectFaceTol:
                            continue

                        oldEdgeNum = len(boundaryEdgesList)
                        Utils.addElementToCompoundArray(projGeoShape, boundaryElementsList, boundaryEdgesList, boundaryVertexesList)
                        newEdgeNum = len(boundaryEdgesList)
                        numGenEdges = newEdgeNum - oldEdgeNum

                        for i in range(numGenEdges):
                            identifier = self.makeIdentifier([f"{id}"], "Edge", i, "Intersection", faceIdentifier)
                            identifierList.append(identifier)
                            element = (obj.Boundary, f"Edge{str(oldEdgeNum + (i + 1))}")
                            
                            self.updateElement(element, identifier, elementMap)
                            occurence += 1

                    geoShape = geo.toShape()
                    geoShape.Orientation = "Reversed"
                    geoShape.Placement = endExtrudePoint
                    oldVertNum = len(boundaryVertexesList)

                    # boundaryShape = Part.Compound([boundaryShape, geoShape])
                    Utils.addElementToCompoundArray(geoShape, boundaryElementsList, boundaryEdgesList, boundaryVertexesList)

                    newVertNum = len(boundaryVertexesList)
                    newVertexList = boundaryVertexesList[oldVertNum:newVertNum]

                    for i, vec in enumerate(newVertexList):
                        point = basePoint.inverse().multVec((vec.Point - extrudeVector))

                        unsupportedVertexes[f"Vertex{str((i + 1) + oldVertNum)}"] = {"Vector": point, "Type": "SketchProjection"}

                    if isinstance(geoShape, Part.Edge):
                        # Create Base Sketch Boundary
                        identifier = self.makeIdentifier([f"{id}"], "Edge", 0, "SketchProjection")
                        identifierList.append(identifier)
                        element = (obj.Boundary, f"Edge{str(len(boundaryEdgesList))}")
                        
                        self.updateElement(element, identifier, elementMap)

            createPointsTime = time.time() - startTime

            App.Console.PrintLog(f"{obj.Label} create points time: {str(createPointsTime)}\n")

            geoIDs = []

            # Generate WiresBoundary and map Vertexes appended by the prior loop
            for _,v in points.items():
                # Start with edges
                if extrudeLength != 0:
                    startPoint = v["Vector"]
                    endPoint = v["Vector"] + App.Vector(0, 0, extrudeLength)
                    
                    line = Part.LineSegment(startPoint, endPoint).toShape()
                    line.Placement = basePoint
                    oldVertNum = len(boundaryVertexesList)
                    # boundaryShape = Part.Compound([boundaryShape, line])
                    Utils.addElementToCompoundArray(line, boundaryElementsList, boundaryEdgesList, boundaryVertexesList)

                    newVertNum = len(boundaryVertexesList)

                    newVertexes = boundaryVertexesList[oldVertNum:newVertNum]
                    startVertex = None
                    endVertex = None

                    if newVertexes[0].Point.isEqual(startPoint, tol):
                        startVertex = f"Vertex{str(oldVertNum+1)}"
                        endVertex = f"Vertex{str(oldVertNum+2)}"
                    elif newVertexes[1].Point.isEqual(startPoint, tol):
                        startVertex = f"Vertex{str(oldVertNum+2)}"
                        endVertex = f"Vertex{str(oldVertNum+1)}"
                    
                    # Handle start vertex
                    identifier = self.makeIdentifier(v["IDs"], "Vertex", 0, "WiresBoundary", extraInfo = "BottomPoint")
                    identifierList.append(identifier)
                    element = (obj.Boundary, startVertex)
                    self.updateElement(element, identifier, elementMap)

                    # Handle end vertex
                    identifier = self.makeIdentifier(v["IDs"], "Vertex", 0, "WiresBoundary", extraInfo = "TopPoint")
                    identifierList.append(identifier)
                    element = (obj.Boundary, endVertex)
                    self.updateElement(element, identifier, elementMap)

                    # Handle wire boundary
                    identifier = self.makeIdentifier(v["IDs"], "Edge", 0, "WiresBoundary")
                    identifierList.append(identifier)
                    element = (obj.Boundary, f"Edge{str(len(boundaryEdgesList))}")
                    self.updateElement(element, identifier, elementMap)

                # Handle old loop vertexes
                for elementName, unsupportedVertex in unsupportedVertexes.items():
                    if v["Vector"].isEqual(unsupportedVertex["Vector"], tol):
                        identifier = self.makeIdentifier(v["IDs"], "Vertex", geoIDs.count(v["IDs"]), unsupportedVertex["Type"])
                        identifierList.append(identifier)
                        element = (obj.Boundary, elementName)
                        self.updateElement(element, identifier, elementMap)

                        geoIDs.append(v["IDs"])
            
            for hash, value in elementMap.copy().items():
                if value["Identifier"] not in identifierList:
                    # elementMap.pop(hash)
                    elementMap[hash]["Stale"] = True

            App.Console.PrintLog(f"{obj.Label} time taken in applying map: {str((time.time() - startTime) - createPointsTime)}\n")
            App.Console.PrintLog(f"{obj.Label} time taken in updateElement: {str(self.timeTakeUE)}\n")
            App.Console.PrintLog(f"{obj.Label} total boundary time: {str(time.time() - startTime)}\n")

            obj.ElementMap = json.dumps(elementMap)
            boundaryElementsList = GeometryUtils.mapElementsFromMap(boundaryEdgesList, boundaryVertexesList, elementMap)
            boundaryShape = Part.makeCompound(boundaryElementsList)

            obj.Boundary.Shape = boundaryShape
            obj.Boundary.ViewObject.LineWidth = Constants.boundaryLineWidth
            obj.Boundary.ViewObject.PointSize = Constants.boundaryPointSize

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
        super(Extrusion, self).onChanged(obj, prop)
            
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
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None
    
def makeExtrusion(container=None, support=None, showGui = True):
    if container is None:
        container = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")

    if container is not None and hasattr(container, "Type") and container.Type == "PartContainer":
        if support is None:
            selectedObject = Gui.Selection.getSelection()
            if len(selectedObject) == 0:
                support = None
            else:
                support = selectedObject[0]
        else:
            selectedObject = support # Rename for clarity in the existing logic

        doc = container.Document
        doc.openTransaction("CreateExtrusion")

        if support is not None and Utils.isType(support, Constants.supportTypes):
            obj = doc.addObject("Part::FeaturePython", "Extrusion")
            boundary = doc.addObject("Part::Feature", "Boundary")
            boundary.addProperty("App::PropertyString", "Type")
            boundary.Type = "Boundary"

            boundary.ViewObject.ShowInTree = True

            Extrusion(obj)
            ViewProviderExtrusion(obj.ViewObject)

            obj.Proxy.setSupport(obj, support)
            obj.Proxy.setBoundary(obj, boundary)

            container.Proxy.addObject(container, obj, True)
            container.Proxy.setTip(container, obj)

            if showGui:
                obj.Proxy.showGui(obj)

            return obj
        else:
            App.Console.PrintError("Selected object is not a sketch!\n")
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")
    
    return None