import FreeCAD as App
import FreeCADGui as Gui
import Part
import sys
import math
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from Utils.Utils import getIDsFromSelection, getElementFromHash, generateHashName, getObjectsFromScope
from Utils.GuiUtils import SelectorWidget
from Utils.Preferences import *
from PySide import QtWidgets
import json
from Entities.Feature import Feature

dressupPropertyNames = ["Radius", "Length", "Diameter", "Angle"]

# 0 for Fillet
# 1 for Chamfer
# 2 for Countersink

class DressupTaskPanel:
    def __init__(self, obj, addOldSelection=True, startSelection=[]):
        self.form = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.form)
        layout.addWidget(QtWidgets.QLabel("Editing: " + obj.Label))

        button_layout = QtWidgets.QHBoxLayout()

        self.applyButton = QtWidgets.QPushButton("Apply")
        self.updateButton = QtWidgets.QPushButton("Update")
        self.cancelButton = QtWidgets.QPushButton("Cancel")

        button_layout.addWidget(self.applyButton)
        button_layout.addWidget(self.updateButton)
        button_layout.addWidget(self.cancelButton)

        layout.addLayout(button_layout)
        
        self.applyButton.clicked.connect(self.accept)
        self.updateButton.clicked.connect(self.update)
        self.cancelButton.clicked.connect(self.reject)

        self.oldHashes = obj.Edges

        self.dressup = obj
        self.container = self.dressup.Proxy.getContainer(self.dressup)
        self.selector = SelectorWidget(addOldSelection=addOldSelection, startSelection=startSelection, container=self.container)
        layout.addWidget(self.selector)

        if self.dressup.DressupType == 0:
            self.oldRadius = self.dressup.Radius

            radius_row = QtWidgets.QHBoxLayout()
            radius_label = QtWidgets.QLabel("Radius:")
            self.radius_input = QtWidgets.QDoubleSpinBox()
            self.radius_input.setMinimum(0)
            self.radius_input.setMaximum(100000)
            self.radius_input.setSingleStep(1)
            self.radius_input.setValue(self.oldRadius)

            radius_row.addWidget(radius_label)
            radius_row.addWidget(self.radius_input)
            radius_row.addStretch()

            layout.addLayout(radius_row)
        elif self.dressup.DressupType == 1:
            self.oldLength = self.dressup.Length

            lengthRow = QtWidgets.QHBoxLayout()
            lengthLabel = QtWidgets.QLabel("Length:")
            self.lengthInput = QtWidgets.QDoubleSpinBox()
            self.lengthInput.setMinimum(0)
            self.lengthInput.setMaximum(100000)
            self.lengthInput.setSingleStep(1)
            self.lengthInput.setValue(self.oldLength)

            lengthRow.addWidget(lengthLabel)
            lengthRow.addWidget(self.lengthInput)
            lengthRow.addStretch()

            layout.addLayout(lengthRow)
        elif self.dressup.DressupType == 2:
            self.oldDiameter = self.dressup.Diameter
            self.oldAngle = self.dressup.Angle

            counterSinkRow = QtWidgets.QHBoxLayout()
            diameterLabel = QtWidgets.QLabel("Diameter:")
            self.diameterInput = QtWidgets.QDoubleSpinBox()
            self.diameterInput.setMinimum(0)
            self.diameterInput.setMaximum(100000)
            self.diameterInput.setSingleStep(1)
            self.diameterInput.setValue(self.oldDiameter)

            angleLabel = QtWidgets.QLabel("Angle:")
            self.angleInput = QtWidgets.QDoubleSpinBox()
            self.angleInput.setMinimum(0)
            self.angleInput.setMaximum(180)
            self.angleInput.setSingleStep(10)
            self.angleInput.setValue(self.oldAngle)

            counterSinkRow.addWidget(diameterLabel)
            counterSinkRow.addWidget(self.diameterInput)
            
            counterSinkRow.addWidget(angleLabel)
            counterSinkRow.addWidget(self.angleInput)

            counterSinkRow.addStretch()

            layout.addLayout(counterSinkRow)
    
    def update(self):
        selected = self.selector.getSelection()

        if self.dressup.DressupType == 0:
            radius = self.radius_input.value()
            
            self.dressup.Radius = radius
        elif self.dressup.DressupType == 1:
            length = self.lengthInput.value()
            
            self.dressup.Length = length
        elif self.dressup.DressupType == 2:
            diameter = self.diameterInput.value()
            self.dressup.Diameter = diameter

            angle = self.angleInput.value()
            self.dressup.Angle = angle

        self.dressup.Edges = selected
        self.container.recompute()
    
    def accept(self):
        self.update()

        self.selector.cleanup()
        Gui.Control.closeDialog()

    def reject(self):
        self.dressup.Edges = self.oldHashes

        if self.dressup.DressupType == 0:
            self.dressup.Radius = self.oldRadius
        elif self.dressup.DressupType == 1:
            self.dressup.Length = self.oldLength
        elif self.dressup.DressupType == 2:
            self.dressup.Diameter = self.oldDiameter
            self.dressup.Angle = self.oldAngle

        # self.container.recompute()
        self.selector.cleanup()
        Gui.Control.closeDialog()

    def getStandardButtons(self):
        return 0

    def getTitle(self):
        return "Dressup Task Panel"

    def IsModal(self):
        return False

class FeatureDressup(Feature):
    def __init__(self, obj, dressupType):
        obj.Proxy = self
        self.updateProps(obj, dressupType)
    
    def showGui(self, obj, addOldSelection = True, startSelection = []):
        Gui.Control.showDialog(DressupTaskPanel(obj, addOldSelection, startSelection))
    
    def getIndividualShapes(self, obj):
        if obj.DressupType == 2:
            if hasattr(obj, "IndividualShape"):
                return {0: {"Shape": obj.IndividualShape, "Remove": True}}
            else:
                return {}
        else:
            container = self.getContainer(obj)
            features = container.Proxy.getGroup(container, False, True)
            index = features.index(obj)
            prevShape = features[index - 1].Shape
            
            removeShape = prevShape.cut(obj.Shape)
            addShape = obj.Shape.cut(prevShape)

            return {0: {"Shape": removeShape, "Remove": True}, 1: {"Shape": addShape, "Remove": False}}

    def updateProps(self, obj, dressupType = 0):
        hasIndividualShape = False

        if dressupType == 2:
            hasIndividualShape = True

        super(FeatureDressup, self).updateProps(obj, hasIndividualShape, False)

        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
        
        if not hasattr(obj, "DressupType"):
            obj.addProperty("App::PropertyInteger", "DressupType", "ConstraintDesign", "Type of feature dressup.\n0 for fillet\n1 for chamfer")
            obj.DressupType = dressupType
            obj.setEditorMode("DressupType", 3)
        
        if hasattr(obj, "DressupType") and obj.DressupType == 0:
            obj.Type = "Fillet"

            if not hasattr(obj, "Radius"):
                obj.addProperty("App::PropertyFloat", "Radius", "ConstraintDesign", "Radius of fillet.")
                obj.Radius = 1.0
        elif hasattr(obj, "DressupType") and obj.DressupType == 1:
            obj.Type = "Chamfer"

            if not hasattr(obj, "Length"):
                obj.addProperty("App::PropertyFloat", "Length", "ConstraintDesign", "Length of fillet.")
                obj.Length = 1.0
        elif hasattr(obj, "DressupType") and obj.DressupType == 2:
            obj.Type = "Countersink"

            if not hasattr(obj, "Diameter"):
                obj.addProperty("App::PropertyFloat", "Diameter", "ConstraintDesign", "Diameter of the countersink.")
                obj.Diameter = 8

            if not hasattr(obj, "Angle"):
                obj.addProperty("App::PropertyFloat", "Angle", "ConstraintDesign", "Angle of the countersink in degrees.")
                obj.Angle = 90

            if not hasattr(obj, "Reversed"):
                obj.addProperty("App::PropertyBool", "Reversed", "ConstraintDesign", "Determines if the countersinks should be reversed.")
                obj.Angle = 90

            if not hasattr(obj, "Boundary"):
                obj.addProperty("App::PropertyXLink", "Boundary", "ConstraintDesign", "Boundary of this dressup")
            
            if not hasattr(obj, "Group"):
                obj.addProperty("App::PropertyLinkList", "Group", "ConstraintDesign", "Group of this dressup")

        if not hasattr(obj, "Edges"):
            obj.addProperty("App::PropertyStringList", "Edges", "ConstraintDesign", "Edges to fillet.")
    
    def generateEquations(self):
        pass

    def generateParameters(self):
        pass

    def getConstrainedElements(self):
        pass

    def getContainer(self, obj):
        return super(FeatureDressup, self).getContainer(obj)
    
    def makeIdentifier(self, supportHash, placement, elementType):
        """ Used to make development easier, won't need to update 10 different instances of id generation """
        return f"{supportHash};{placement};{elementType}"

    # {"<String ID>": {"Identifier": "<SupportHash>;Top/Bottom;ElementType", "Element": <BoundaryName>.<Vertex1/Edge2/Face3>}}
    def updateElement(self, map, identifier, element):
        foundElement = False

        for stringId, value in map.items():
            if value["Identifier"] == identifier:
                foundElement = True

                map[stringId]["Element"] = f"{element[0].Name}.{element[1]}"
        
        if not foundElement:
            newId = generateHashName(map)

            map[newId] = {"Identifier": identifier, "Element": f"{element[0].Name}.{element[1]}"}
        
        return map
        
    def generateShape(self, obj, prevShape):
        if prevShape.isNull():
            raise Exception("No feature before this fillet!")

        datumEdges = obj.Edges
        allShapeEdges = prevShape.Edges
        elementsToDressup = {}
        container = self.getContainer(obj)
        identifiers = []
        skipHashes = []

        self.updateProps(obj, obj.DressupType)

        if hasattr(obj, "Boundary") and obj.Boundary == None:
            boundary = makeBoundary(obj.Document)

            container.Proxy.addObject(container, boundary, False) # needed for global placement
            obj.Boundary = boundary

        if container == None:
            App.Console.PrintError(obj.Label + " is unable to find parent container!")

            return prevShape
        else:
            for edge in allShapeEdges:
                if edge.isValid():
                    for stringID in datumEdges:
                        if stringID in skipHashes: continue

                        try:
                            element = getElementFromHash(container, stringID)
                        except Exception as e:
                            App.Console.PrintError(str(e) + "\n")
                            continue
                        
                        if element == None or (element[0] == None or (len(element) == 2 and element[1] == None)):
                            continue
                        
                        if element != None:
                            datumEdge = element[0].Shape.getElement(element[1])
                            correctEdge = False
                            intersectionPoints = 0

                            if edge.CenterOfMass.isEqual(datumEdge.CenterOfMass, 1e-2):
                                correctEdge = True
                            else:
                                try:
                                    if not ((edge.Curve.TypeId == datumEdge.Curve.TypeId) or (edge.Curve.TypeId == "Part::GeomBSplineCurve" and datumEdge.Curve.TypeId == "Part::GeomCircle")):
                                        correctEdge = False
                                    else:
                                        print("run intersection test")
                                        try:
                                            intersectionPoints = len(edge.Curve.intersectCC(datumEdge.Curve))
                                        except:
                                            intersectionPoints = -1
                                        
                                        if intersectionPoints > 2 or intersectionPoints == -1:
                                            correctEdge = True
                                except:
                                    correctEdge = False
                            
                            try:
                                if correctEdge:
                                    # elementsToDressup.append(edge)
                                    print(stringID)
                                    _, _, _, singleID = getObjectsFromScope(container, stringID)
                                    elementsToDressup[singleID] = edge

                                    print(f"add hash: {singleID}")
                            except Exception as e:
                                print(e)
                        else:
                            skipHashes.append(stringID)
                    dressupShape = prevShape
            
            if len(elementsToDressup) != 0:
                if hasattr(obj, "DressupType") and obj.DressupType == 0:
                    try:
                        dressupShape = prevShape.makeFillet(obj.Radius, list(elementsToDressup.values()))
                    except Exception as e:
                        dressupShape = prevShape
                        App.Console.PrintError(obj.Label + ": creating a fillet with the radius of " + str(obj.Radius) + " failed!\nException: " + str(e) + "\n")
                elif hasattr(obj, "DressupType") and obj.DressupType == 1:
                    try:
                        dressupShape = prevShape.makeChamfer(obj.Length, list(elementsToDressup.values()))
                    except Exception as e:
                        dressupShape = prevShape
                        App.Console.PrintError(obj.Label + ": creating a chamfer with the length of " + str(obj.Length) + " failed!\nException: " + str(e) + "\n")
                elif hasattr(obj, "DressupType") and obj.DressupType == 2:
                    try:
                        depth = obj.Diameter/2 * math.tan((math.radians(obj.Angle)) / 2)

                        # I have two of these to save on possible computation time, I should't need to constantly recreate
                        # the cone each time.
                        forwardCone = Part.makeCone(obj.Diameter/2, 0, depth, App.Vector(0,0,0), App.Vector(0,0,1), 360)
                        reversedCone = Part.makeCone(obj.Diameter/2, 0, depth, App.Vector(0,0,0), App.Vector(0,0,-1), 360)
                        cutCompoundArray = []
                        map = json.loads(obj.ElementMap)
                        boundaryShape = Part.Shape()

                        for hash, edge in elementsToDressup.items():
                            print(edge.Orientation)

                            forward = True

                            if edge.Orientation == "Forward":
                                forward = True
                            else:
                                forward = False

                            if obj.Reversed:
                                forward = not forward

                            if edge.Curve.TypeId == "Part::GeomCircle":
                                radius = edge.Curve.Radius
                                placement = App.Placement()
                                placement.Base = edge.CenterOfMass
                                placement.Rotation = edge.Placement.Rotation

                                topCircle = Part.Circle()
                                topCircle.Radius = obj.Diameter/2
                                topCircleSh = topCircle.toShape()
                                topCircleSh.Placement = placement

                                boundaryShape = Part.Compound([boundaryShape, topCircleSh])
                                identifier = self.makeIdentifier(hash, "Top", "Edge")
                                identifiers.append(identifier)
                                map = self.updateElement(map, identifier, (obj.Boundary, f"Edge{str(len(boundaryShape.Edges))}"))

                                thetaRad = math.radians(obj.Angle / 2)
                                deltaR = obj.Diameter/2 - radius
                                slantDist = deltaR * math.tan(thetaRad)

                                if not forward:
                                    slantDist *= -1

                                print(slantDist)

                                moveVector = topCircleSh.Curve.Axis.normalize().multiply(slantDist)

                                bottomCircle = Part.Circle()
                                bottomCircle.Radius = radius
                                bottomCircleSh = bottomCircle.toShape()
                                bottomCircleSh.Placement = placement
                                bottomCircleSh.Placement.Base += moveVector

                                boundaryShape = Part.Compound([boundaryShape, bottomCircleSh])
                                identifier = self.makeIdentifier(hash, "Bottom", "Edge")
                                identifiers.append(identifier)
                                map = self.updateElement(map, identifier, (obj.Boundary, f"Edge{str(len(boundaryShape.Edges))}"))

                                if forward:
                                    forwardCone.Placement = placement
                                    cutCompoundArray.append(forwardCone.copy())
                                else:
                                    reversedCone.Placement = placement
                                    cutCompoundArray.append(reversedCone.copy())
                            else:
                                print("edge is not a circle")

                        for k,v in map.copy().items():
                            if v["Identifier"] not in identifiers:
                                map.pop(k)
                        
                        obj.Boundary.Shape = boundaryShape
                        obj.ElementMap = json.dumps(map)
                        cutCompound = Part.Compound(cutCompoundArray)
                        obj.IndividualShape = cutCompound.copy()
                        dressupShape = prevShape.cut(cutCompound)

                        obj.Boundary.purgeTouched()
                    except Exception as e:
                        dressupShape = prevShape
                        App.Console.PrintError(obj.Label + ": creating a countersink failed!\nException: " + str(e) + "\n")
            else:
                dressupShape = prevShape
            
            obj.Shape = dressupShape

            return dressupShape
    
    # Format {"HashName": {"Edge:" edge, "GeoTag", sketchGeoTag}}

    def getBoundaries(self, obj, isShape=False):
        if hasattr(obj, "Boundary"):
            if isShape:
                return [obj.Boundary.Shape]
            else:
                return [obj.Boundary]
        else:
            return []

    def execute(self, obj):
        self.updateProps(obj)
            
    def onChanged(self, obj, prop):
        if prop in dressupPropertyNames:
            obj.touch()
        
        if prop == "Boundary":
            obj.Group = [obj.Boundary]
        
        super(FeatureDressup, self).onChanged(obj, prop)
            
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

class ViewProviderDressup:
    def __init__(self, obj):
        obj.Proxy = self
        obj.Selectable = False
        self.Origin = None
    
    def onDelete(self, vobj, subelements):
        try:
            container = vobj.Object.Proxy.getContainer(vobj.Object)
            container.Proxy.fixTip(container)
        except Exception as e:
            App.Console.PrintWarning("Deleting Fillet Errored, reason: " + str(e))
        
        print("delete: fillet")

        return True
    
    def attach(self, vobj):
        # Called when the view provider is attached
        self.Object = vobj
        self.Object.Selectable = False

        return

    def setEdit(self, vobj, mode):
        vobj.Object.Document.openTransaction("EditDressup")
        vobj.Object.Proxy.showGui(vobj.Object, False, vobj.Object.Edges)

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
        if self.Object.Object.DressupType == 0:
            return os.path.join(os.path.dirname(__file__), "..", "icons", "Fillet.svg")
        elif self.Object.Object.DressupType == 1:
            return os.path.join(os.path.dirname(__file__), "..", "icons", "Chamfer.svg")
        elif self.Object.Object.DressupType == 2:
            return os.path.join(os.path.dirname(__file__), "..", "icons", "Countersink.svg")
        else:
            return """
                /* XPM */
                static const char *icon[] = {
                "16 16 2 1",
                "  c None",
                ". c #0000FF",
                "                ",
                "    ........    ",
                "   ..........   ",
                "  ............  ",
                " .............. ",
                " .............. ",
                " .............. ",
                " .............. ",
                " .............. ",
                " .............. ",
                " .............. ",
                " .............. ",
                "  ............  ",
                "   ..........   ",
                "    ........    ",
                "                "
                };
            """
    
    def claimChildren(self):
        if hasattr(self, "Object") and hasattr(self.Object.Object, "Group") and self.Object.Object.DressupType == 2:
            if len(self.Object.Object.Group) == 0:
                self.Object.Object.Group = [self.Object.Object.Boundary]
                
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

def makeBoundary(document):
    boundary = document.addObject("Part::Feature", "Boundary")
    boundary.addProperty("App::PropertyString", "Type")
    boundary.Type = "Boundary"

    return boundary

""" Method to create a FeatureDressup. """
def makeDressup(dressupType):
    activeObject = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")

    if activeObject != None and hasattr(activeObject, "Type") and activeObject.Type == "PartContainer":
        name = "Dressup"
        doc = activeObject.Document
        doc.openTransaction("CreateDressup")

        if dressupType == 0:
            name = "Fillet"
        elif dressupType == 1:
            name = "Chamfer"
        elif dressupType == 2:
            name = "Countersink"

            boundary = makeBoundary(doc)

        obj = App.ActiveDocument.addObject("Part::FeaturePython", name)
        FeatureDressup(obj, dressupType)
        ViewProviderDressup(obj.ViewObject)

        if dressupType == 2:
            obj.Boundary = boundary
            activeObject.Proxy.addObject(activeObject, boundary, False)

        hashes = getIDsFromSelection(Gui.Selection.getCompleteSelection())

        activeObject.Proxy.addObject(activeObject, obj, True)
        activeObject.Proxy.setTip(activeObject, obj)
        obj.Proxy.showGui(obj, True)

        obj.Edges = hashes
        activeObject.recompute()
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")