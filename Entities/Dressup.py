import FreeCAD as App
import FreeCADGui as Gui
import Part
import sys
import math
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from Utils import Utils
from Utils import GuiUtils
from Utils import Constants
from Utils import GeometryUtils
from PySide import QtWidgets
import json
from Entities.Feature import Feature

dressupPropertyNames = ["Radius", "Length", "Diameter", "Angle"]

# 0 for Fillet
# 1 for Chamfer
# 2 for Countersink

class DressupTaskPanel:
    def __init__(self, obj, addOldSelection=True, startSelection=[], deleteAfterCancel = False):
        super(DressupTaskPanel, self).__init__()
        self.form = QtWidgets.QWidget()
        self.form.destroyed.connect(self.accept) # run immediatly incase something else errors

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
        self.selector = GuiUtils.SelectorWidget(addOldSelection=addOldSelection, startSelection=startSelection, container=self.container)
        layout.addWidget(self.selector)

        self.deleteAfterCancel = deleteAfterCancel

        if self.dressup.DressupType == 0:
            self.radiusUnitMult = self.dressup.Radius.getUserPreferred()[1]
            self.oldRadius = self.dressup.Radius.Value

            radius_row = QtWidgets.QHBoxLayout()
            radius_label = QtWidgets.QLabel("Radius:")
            self.radius_input = QtWidgets.QDoubleSpinBox()
            self.radius_input.setMinimum(0)
            self.radius_input.setMaximum(100000)
            self.radius_input.setSingleStep(1)
            self.radius_input.setValue(self.oldRadius / self.radiusUnitMult)

            radius_row.addWidget(radius_label)
            radius_row.addWidget(self.radius_input)
            radius_row.addStretch()

            layout.addLayout(radius_row)
        elif self.dressup.DressupType == 1:
            if hasattr(self.dressup.Length, 'getUserPreferred'):
                self.lengthUnitMult = self.dressup.Length.getUserPreferred()[1]
                self.oldLength = self.dressup.Length.Value
            else:
                self.lengthUnitMult = 1
                self.oldLength = self.dressup.Length

            lengthRow = QtWidgets.QHBoxLayout()
            lengthLabel = QtWidgets.QLabel("Length:")
            self.lengthInput = QtWidgets.QDoubleSpinBox()
            self.lengthInput.setMinimum(0)
            self.lengthInput.setMaximum(100000)
            self.lengthInput.setSingleStep(1)
            self.lengthInput.setValue(self.oldLength / self.lengthUnitMult)

            lengthRow.addWidget(lengthLabel)
            lengthRow.addWidget(self.lengthInput)
            lengthRow.addStretch()

            layout.addLayout(lengthRow)
        elif self.dressup.DressupType == 2:
            if hasattr(self.dressup.Diameter, 'getUserPreferred'):
                self.diameterUnitMult = self.dressup.Diameter.getUserPreferred()[1]
                self.oldDiameter = self.dressup.Diameter.Value
            else:
                self.diameterUnitMult = 1
                self.oldDiameter = self.dressup.Diameter
            if hasattr(self.dressup.Angle, 'Value'):
                self.oldAngle = self.dressup.Angle.Value
            else:
                self.oldAngle = self.dressup.Angle

            counterSinkRow = QtWidgets.QHBoxLayout()
            diameterLabel = QtWidgets.QLabel("Diameter:")
            self.diameterInput = QtWidgets.QDoubleSpinBox()
            self.diameterInput.setMinimum(0)
            self.diameterInput.setMaximum(100000)
            self.diameterInput.setSingleStep(1)
            self.diameterInput.setValue(self.oldDiameter / self.diameterUnitMult)

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
            radius = self.radius_input.value() * self.radiusUnitMult
            self.dressup.Radius.Value = radius
        elif self.dressup.DressupType == 1:
            length = self.lengthInput.value()
            if hasattr(self.dressup.Length, 'Value'):
                self.dressup.Length.Value = (length * self.lengthUnitMult)
            else:
                self.dressup.Length = length
        elif self.dressup.DressupType == 2:
            diameter = self.diameterInput.value()
            if hasattr(self.dressup.Diameter, 'Value'):
                self.dressup.Diameter.Value = (diameter * self.diameterUnitMult)
            else:
                self.dressup.Diameter = diameter

            angle = self.angleInput.value()
            if hasattr(self.dressup.Angle, 'Value'):
                self.dressup.Angle.Value = angle
            else:
                self.dressup.Angle = angle

        self.dressup.Edges = selected
        self.container.recompute()
    
    def accept(self):
        self.update()

        self.close()

        return True

    def close(self):
        self.selector.cleanup()
        Gui.Control.closeDialog()

    def reject(self, obj=None):
        self.dressup.Edges = self.oldHashes

        if self.dressup.DressupType == 0:
            self.dressup.Radius.Value = self.oldRadius
        elif self.dressup.DressupType == 1:
            if hasattr(self.dressup.Length, 'Value'):
                self.dressup.Length.Value = self.oldLength
            else:
                self.dressup.Length = self.oldLength
        elif self.dressup.DressupType == 2:
            if hasattr(self.dressup.Diameter, 'Value'):
                self.dressup.Diameter.Value = self.oldDiameter
            else:
                self.dressup.Diameter = self.oldDiameter
            if hasattr(self.dressup.Angle, 'Value'):
                self.dressup.Angle.Value = self.oldAngle
            else:
                self.dressup.Angle = self.oldAngle

        # self.container.recompute()
        
        self.close()

        if self.deleteAfterCancel:
            container = self.dressup.Proxy.getContainer(self.dressup)

            if container:
                container.Document.openTransaction("DeleteDressup")
                container.Proxy.deleteChild(container, self.dressup)

        return True

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
    
    def showGui(self, obj, addOldSelection = True, startSelection = [], deleteAfterCancel = False):
        Gui.Control.showDialog(DressupTaskPanel(obj, addOldSelection, startSelection, deleteAfterCancel))
    
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

            if (not hasattr(obj, "Radius")
                or obj.getTypeIdOfProperty("Radius") == "App::PropertyFloat"
            ):
                newVal = 1.0
                if hasattr(obj, "Radius"):
                    if hasattr(obj.Radius, "Value"):
                        newVal = obj.Radius.Value
                    else:
                        newVal = obj.Radius
                    obj.removeProperty("Radius")
                obj.addProperty("App::PropertyDistance", "Radius", "ConstraintDesign", "Radius of fillet.")
                obj.Radius.Value = newVal
            
            if not hasattr(obj, "IndividualFillet"):
                obj.addProperty("App::PropertyBool", "IndividualFillet", "ConstraintDesign", "This fillets each edge individually, then uses boolean operations to merge them together.")
                obj.IndividualFillet = False
        elif hasattr(obj, "DressupType") and obj.DressupType == 1:
            obj.Type = "Chamfer"

            if (not hasattr(obj, "Length")
                or obj.getTypeIdOfProperty("Length") == "App::PropertyFloat"
            ):
                newVal = 1.0
                if hasattr(obj, "Length"):
                    if hasattr(obj.Length, "Value"):
                        newVal = obj.Length.Value
                    else:
                        newVal = obj.Length
                    obj.removeProperty("Length")
                obj.addProperty("App::PropertyDistance", "Length", "ConstraintDesign", "Length of fillet.")
                obj.Length.Value = newVal
        elif hasattr(obj, "DressupType") and obj.DressupType == 2:
            obj.Type = "Countersink"

            if (not hasattr(obj, "Diameter")
                or obj.getTypeIdOfProperty("Diameter") == "App::PropertyFloat"
            ):
                newVal = 8
                if hasattr(obj, "Diameter"):
                    if hasattr(obj.Diameter, "Value"):
                        newVal = obj.Diameter.Value
                    else:
                        newVal = obj.Diameter
                    obj.removeProperty("Diameter")
                obj.addProperty("App::PropertyDistance", "Diameter", "ConstraintDesign", "Diameter of the countersink.")
                obj.Diameter.Value = newVal

            if (not hasattr(obj, "Angle")
                or obj.getTypeIdOfProperty("Angle") == "App::PropertyFloat"
                or obj.getTypeIdOfProperty("Angle") == "App::PropertyAngle"
            ):
                newVal = 90
                if hasattr(obj, "Angle"):
                    if hasattr(obj.Angle, "Value"):
                        newVal = obj.Angle.Value
                    else:
                        newVal = obj.Angle
                    obj.removeProperty("Angle")
                obj.addProperty("App::PropertyAngle", "Angle", "ConstraintDesign", "Angle of the countersink in degrees.")
                obj.Angle.Value = newVal

            if not hasattr(obj, "Reversed"):
                obj.addProperty("App::PropertyBool", "Reversed", "ConstraintDesign", "Determines if the countersinks should be reversed.")

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

    # {"<String ID>": {"Identifier": "<SupportHash>;Top/Bottom;ElementType", "Stale": <True/False>, "Element": <BoundaryName>.<Vertex1/Edge2/Face3>}}
    def updateElement(self, map, identifier, element):
        foundElement = False

        for stringId, value in map.items():
            if value["Identifier"] == identifier:
                foundElement = True

                map[stringId]["Element"] = f"{element[0].Name}.{element[1]}"
                map[stringId]["Stale"] = False
        
        if not foundElement:
            newId = Utils.generateHashName(map)

            map[newId] = {"Identifier": identifier, "Stale": False, "Element": f"{element[0].Name}.{element[1]}"}
        
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
            if hasattr(obj, "DressupType"):
                if obj.DressupType != 2:
                    for edge in allShapeEdges:
                        if edge.isValid():
                            for stringID in datumEdges:
                                if stringID in skipHashes: continue
                                try:
                                    element = Utils.getElementFromHash(container, stringID, requestingObjectLabel=obj.Label)
                                except Exception as e:
                                    App.Console.PrintError(str(e) + "\n")
                                    continue

                                if element[0] != None:
                                    datumEdge = element[0].Shape.getElement(element[1])
                                    correctEdge = False
                                    intersectionPoints = 0

                                    # try:
                                        # if edge.CenterOfMass.isEqual(datumEdge.CenterOfMass, 1e-2):
                                        #     correctEdge = True
                                        # else:
                                        #     if not ((edge.Curve.TypeId == datumEdge.Curve.TypeId) or (edge.Curve.TypeId == "Part::GeomBSplineCurve" and datumEdge.Curve.TypeId == "Part::GeomCircle")):
                                        #         correctEdge = False
                                        #     else:
                                        #         try:
                                        #             intersectionPoints = len(edge.Curve.intersectCC(datumEdge.Curve))
                                        #         except:
                                        #             intersectionPoints = -1
                                                
                                        #         if intersectionPoints > 2 or intersectionPoints == -1:
                                        #             correctEdge = True
                                    if GeometryUtils.doEdgesIntersect(edge, datumEdge):
                                        correctEdge = True
                                    # except Exception as e:
                                        # print(f"exception while checking: {str(e)}")
                                        # correctEdge = False
                                    
                                    try:
                                        if correctEdge:
                                            # elementsToDressup.append(edge)
                                            _, _, _, singleID = Utils.getObjectsFromScope(container, stringID)
                                            elementsToDressup[singleID] = edge

                                    except Exception as e:
                                        print(e)
                                else:
                                    skipHashes.append(stringID)
            
            dressupShape = prevShape
            if hasattr(obj, "DressupType") and obj.DressupType == 0:
                try:
                    if len(elementsToDressup) != 0:
                        if obj.IndividualFillet:
                            cutShapeList = []
                            fuseShapeList = []

                            for stringID, filletElement in elementsToDressup.items():
                                try:
                                    filletShape = prevShape.makeFillet((obj.Radius.Value if hasattr(obj.Radius, 'Value') else obj.Radius), filletElement)

                                    cutShapeList.append(prevShape.cut(filletShape))
                                    fuseShapeList.append(filletShape.cut(prevShape))
                                except:
                                    App.Console.PrintError(obj.Label + ": creating a fillet with the radius of " + str(obj.Radius) + " failed on " + stringID + "!\n")

                        
                            if len(cutShapeList) != 0:
                                dressupShape = dressupShape.cut(Part.makeCompound(cutShapeList))
                            
                            if len(fuseShapeList) != 0:
                                dressupShape = dressupShape.fuse(Part.makeCompound(fuseShapeList))
                        else:
                            dressupShape = prevShape.makeFillet((obj.Radius.Value if hasattr(obj.Radius, 'Value') else obj.Radius), list(elementsToDressup.values()))
                except Exception as e:
                    App.Console.PrintError(obj.Label + ": creating a fillet with the radius of " + str(obj.Radius) + " failed!\n")
            elif hasattr(obj, "DressupType") and obj.DressupType == 1:
                try:
                    if len(elementsToDressup) != 0:
                        dressupShape = prevShape.makeChamfer((obj.Length.Value if hasattr(obj.Length, 'Value') else obj.Length), list(elementsToDressup.values()))
                except Exception as e:
                    dressupShape = prevShape
                    App.Console.PrintError(obj.Label + ": creating a chamfer with the length of " + str(obj.Length) + " failed!\nException: " + str(e) + "\n")
            elif hasattr(obj, "DressupType") and obj.DressupType == 2:
                    try:
                        depth = ( (obj.Diameter.Value if hasattr(obj.Diameter, 'Value') else obj.Diameter)/2 ) * math.tan((math.radians((obj.Angle.Value if hasattr(obj.Angle, 'Value') else obj.Angle))) / 2)

                        # I have two of these to save on possible computation time, I should't need to constantly recreate
                        # the cone each time.
                        forwardCone = Part.makeCone((obj.Diameter.Value if hasattr(obj.Diameter, 'Value') else obj.Diameter)/2, 0, depth, App.Vector(0,0,0), App.Vector(0,0,1), 360)
                        reversedCone = Part.makeCone((obj.Diameter.Value if hasattr(obj.Diameter, 'Value') else obj.Diameter)/2, 0, depth, App.Vector(0,0,0), App.Vector(0,0,-1), 360)
                        cutCompoundArray = []
                        map = json.loads(obj.ElementMap)
                        boundaryShape = Part.Shape()

                        for stringID in obj.Edges:
                            fullElement = Utils.getElementFromHash(container, stringID, obj.Label)

                            if fullElement[0] != None:
                                element = fullElement[0].Shape.getElement(fullElement[1])
                                _, _, _, singleID = Utils.getObjectsFromScope(container, stringID)

                                forward = True

                                if element.Orientation == "Forward":
                                    forward = True
                                else:
                                    forward = False

                                if obj.Reversed:
                                    forward = not forward

                                if element.Curve.TypeId == "Part::GeomCircle":
                                    radius = element.Curve.Radius
                                    placement = App.Placement()
                                    placement.Base = element.CenterOfMass
                                    placement.Rotation = element.Placement.Rotation

                                    topCircle = Part.Circle()
                                    topCircle.Radius = (obj.Diameter.Value if hasattr(obj.Diameter, 'Value') else obj.Diameter)/2
                                    topCircleSh = topCircle.toShape()
                                    topCircleSh.Placement = placement

                                    boundaryShape = Part.Compound([boundaryShape, topCircleSh])
                                    identifier = self.makeIdentifier(singleID, "Top", "Edge")
                                    identifiers.append(identifier)
                                    map = self.updateElement(map, identifier, (obj.Boundary, f"Edge{str(len(boundaryShape.Edges))}"))

                                    thetaRad = math.radians((obj.Angle.Value if hasattr(obj.Angle, 'Value') else obj.Angle) / 2)
                                    deltaR = (obj.Diameter.Value if hasattr(obj.Diameter, 'Value') else obj.Diameter)/2 - radius
                                    slantDist = deltaR * math.tan(thetaRad)

                                    if not forward:
                                        slantDist *= -1

                                    moveVector = topCircleSh.Curve.Axis.normalize().multiply(slantDist)

                                    bottomCircle = Part.Circle()
                                    bottomCircle.Radius = radius
                                    bottomCircleSh = bottomCircle.toShape()
                                    bottomCircleSh.Placement = placement
                                    bottomCircleSh.Placement.Base += moveVector

                                    boundaryShape = Part.Compound([boundaryShape, bottomCircleSh])
                                    identifier = self.makeIdentifier(singleID, "Bottom", "Edge")
                                    identifiers.append(identifier)
                                    map = self.updateElement(map, identifier, (obj.Boundary, f"Edge{str(len(boundaryShape.Edges))}"))

                                    if forward:
                                        forwardCone.Placement = placement
                                        cutCompoundArray.append(forwardCone.copy())
                                    else:
                                        reversedCone.Placement = placement
                                        cutCompoundArray.append(reversedCone.copy())

                        for k,v in map.copy().items():
                            if v["Identifier"] not in identifiers:
                                # map.pop(k)
                                map[k]["Stale"] = True
                        
                        obj.Boundary.Shape = boundaryShape
                        obj.Boundary.ViewObject.LineWidth = Constants.boundaryLineWidth
                        obj.Boundary.ViewObject.PointSize = Constants.boundaryPointSize
                        obj.ElementMap = json.dumps(map)
                        cutCompound = Part.Compound(cutCompoundArray)
                        obj.IndividualShape = cutCompound.copy()
                        dressupShape = prevShape.cut(cutCompound)

                        obj.Boundary.purgeTouched()
                    except Exception as e:
                        dressupShape = prevShape
                        App.Console.PrintError(obj.Label + ": creating a countersink failed!\nException: " + str(e) + "\n")
            
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
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None

class ViewProviderDressup:
    def __init__(self, obj):
        obj.Proxy = self
        obj.Selectable = False
        self.Origin = None
    
    def onDelete(self, vobj, subelements):
        try:
            if vobj.Object.DressupType == 2 and vobj.Object.Boundary != None:
                vobj.Object.Document.removeObject(vobj.Object.Boundary.Name)

            container = vobj.Object.Proxy.getContainer(vobj.Object)
            container.Proxy.fixTip(container)
        except Exception as e:
            App.Console.PrintWarning("Deleting Fillet Errored, reason: " + str(e))
        
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
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None

def makeBoundary(document):
    boundary = document.addObject("Part::Feature", "Boundary")
    boundary.addProperty("App::PropertyString", "Type")
    boundary.Type = "Boundary"

    return boundary

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

        hashes = Utils.getIDsFromSelection(Gui.Selection.getCompleteSelection())

        activeObject.Proxy.addObject(activeObject, obj, True)
        activeObject.Proxy.setTip(activeObject, obj)
        obj.Proxy.showGui(obj, addOldSelection = True, startSelection = [], deleteAfterCancel = True)

        obj.Edges = hashes
        activeObject.recompute()
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")