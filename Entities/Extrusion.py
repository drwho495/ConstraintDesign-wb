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
from Utils import isType, getElementFromHash, makeLocater, findElementFromLocater
from Entities.Entity import Entity

class Extrusion(Entity):
    def __init__(self, obj):
        obj.Proxy = self
        self.updateProps(obj)
        
    def updateProps(self, obj):
        if not hasattr(obj, "Suppressed"):
            obj.addProperty("App::PropertyBool", "Suppressed", "ConstraintDesign", "Is feature used.")
            obj.Suppressed = False
        
        if not hasattr(obj, "Support"):
            obj.addProperty("App::PropertyXLink", "Support", "ConstraintDesign", "Support object (ex: A sketch)")
        
        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "Extrusion"

        if not hasattr(obj, "DimensionType"):
            obj.addProperty("App::PropertyEnumeration", "DimensionType", "ConstraintDesign", "Determines the type of dimension that controls the length of extrusion.")
            obj.DimensionType = ["Blind", "UpToEntity"]
            obj.DimensionType = "Blind"
        
        if not hasattr(obj, "UpToEntity"):
            obj.addProperty("App::PropertyString", "UpToEntity", "ConstraintDesign")
            obj.UpToEntity = ""
        
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
    
    def addObject(self, obj, newObj):
        if hasattr(obj, "Group"):
            group = obj.Group
            group.append(newObj)

            print("add " + newObj.Label)

            obj.Group = group
    
    def setSupport(self, obj, support):
        obj.Support = support

        self.addObject(obj, support)
    
    def getContainer(self, obj):
        return super(Extrusion, self).getContainer(obj)

    # Format {"HashName": {"Element:" <ObjectName>.<Edge(X)/Vertex(Y)/Face(Z)>, "Locater": "<StartPoint/Center/Endpoint>; <X>,<Y>,<Z>; <RX>,<RY>,<RZ>; <GeoId>v<VertexNum>; <ElementType>"}}
    # Standardize
    def updateElement(self, obj, map, locater, element=None):
        hasElement = False

        if element == None:
            element = (obj, findElementFromLocater(obj, locater))

            print(element)

        for key, _ in map.items():
            locaterArray = map[key]["Locater"].split("::")
            # location = locaterArray[0]
            identifier = locaterArray[1]

            if identifier == locater.split("::")[1]:
                map[key]["Locater"] = locater
                map[key]["Element"] = str(element[0].Name) + "." + str(element[1])

                hasElement = True

        if hasElement == False:
            hash = super(Extrusion, self).generateHashName(map)
            
            map[hash] = {"Element": str(element[0].Name) + "." + str(element[1]), "Locater": locater}
        
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

            if obj.DimensionType == "Blind":
                extrudeLength = obj.Length
            elif obj.DimensionType == "UpToEntity" and obj.UpToEntity != "":
                boundary, elementName = getElementFromHash(obj, obj.UpToEntity)
                element = boundary.Shape.getElement(elementName)

                startPoint = sketch.Placement.Base
                entityPoint = element.CenterOfMass
                vec = entityPoint - startPoint

                extrudeLength = vec.dot(normal)
            
            if obj.Symmetric:
                ZOffset += -extrudeLength / 2
            
            print("ZOffset: " + str(ZOffset))

            extrudeVector = normal * extrudeLength
            offsetVector = normal * ZOffset

            extrusion = face.extrude(extrudeVector)
            extrusion.Placement.Base = extrusion.Placement.Base + offsetVector

            if not prevShape.isNull():
                if obj.Remove:
                    extrusion = prevShape.cut(extrusion)
                else:
                    extrusion = prevShape.fuse(extrusion)
            
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
            
            # {vec: ["geo1v1", "geo2v2"]}
            supportPoints = {}
            
            for geoF in sketch.GeometryFacadeList:
                geo = geoF.Geometry

                if isinstance(geo, Part.LineSegment) or isinstance(geo, Part.ArcOfCircle):
                    tol = 1e-5
                    hasSPoint = False
                    hasEPoint = False

                    for sPointStr, geoIDs in supportPoints.items():
                        sPointSplit = sPointStr.split(";")
                        sPoint = App.Vector(float(sPointSplit[0]), float(sPointSplit[1]), float(sPointSplit[2]))

                        if sPoint.isEqual(geo.StartPoint, tol):
                            supportPoints[sPointStr] += f"geo{geoF.Id}v1,"
                            hasSPoint = True

                            print(supportPoints[sPointStr])
                            break
                        
                        if sPoint.isEqual(geo.EndPoint, tol):
                            supportPoints[sPointStr] += f"geo{geoF.Id}v2,"
                            hasEPoint = True

                            print(supportPoints[sPointStr])
                            break
                    
                    if not hasSPoint:
                        supportPoints[f"{geo.StartPoint.x};{geo.StartPoint.y};{geo.StartPoint.z};"] = f"geo{geoF.Id}v1,"
                    
                    if not hasEPoint:
                        supportPoints[f"{geo.EndPoint.x};{geo.EndPoint.y};{geo.EndPoint.z};"] = f"geo{geoF.Id}v2,"
            
            for pointStr, geoIDs in supportPoints.items():
                pointStr = pointStr.split(";")
                point = App.Vector(float(pointStr[0]), float(pointStr[1]), float(pointStr[2]))
                print(normal)
                locater = makeLocater("StartPoint", point, normal, geoIDs)

                elementMap = self.updateElement(obj, elementMap, locater)
            
            try:
                mapStr = json.dumps(elementMap)

                obj.ElementMap = mapStr
            except Exception as e:
                App.Console.PrintError("Unable to convert the elementMap into a string!\n" + str(e) + "\n")
            
            return extrusion

    def execute(self, obj):
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
    def __init__(self, vobj):
        vobj.Proxy = self
        # vobj.Selectable = False
        self.Origin = None
    
    def onDelete(self, vobj, subelements):
        return True
    
    def attach(self, vobj):
        # Called when the view provider is attached
        self.Object = vobj
        self.Object.Selectable = False

        return

    def setEdit(self, vobj, mode):
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

            activeObject.Proxy.addObject(activeObject, obj, True)
            activeObject.Proxy.setTip(activeObject, obj)
        else:
            App.Console.PrintError("Selected object is not a sketch!\n")
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")
