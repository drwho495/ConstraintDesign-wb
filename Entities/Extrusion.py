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
from Entities.Entity import SolvableEntity

class Extrusion(SolvableEntity):
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
        
        if not hasattr(obj, "ElementMap"):
            obj.addProperty("App::PropertyString", "ElementMap", "ConstraintDesign", "The element map of this extrusion.")
            obj.ElementMap = "{}"

        if not hasattr(obj, "Remove"):
            obj.addProperty("App::PropertyBool", "Remove", "ConstraintDesign", "Determines the type of boolean operation to perform.")
            obj.Remove = False
        
        if not hasattr(obj, "Group"):
            obj.addProperty("App::PropertyLinkList", "Group", "ConstraintDesign", "Group")
        
        if not hasattr(obj, "Length"):
            obj.addProperty("App::PropertyFloat", "Length", "ConstraintDesign", "Internal storage for length of extrusion. Updated every solve.")
            obj.Length = 10
    
    def setDatums(self, obj, wiresDatum, sketchProjection):
        obj.WiresDatum = wiresDatum
        obj.SketchProjection = sketchProjection
    
    def getDatums(self, obj, isShape=False):
        if isShape:
            return [obj.WiresDatum.Shape, obj.SketchProjection.Shape, obj.Support.Shape]
        else:
            return [obj.WiresDatum, obj.SketchProjection, obj.Support]
        
    def setSupport(self, obj, support):
        obj.Support = support
    
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
            hash = super(Extrusion, self).generateHashName(map)
            
            map[hash] = {"Element": str(element[0].Name) + "." + str(element[1]), "GeoId": id, "Occurrence": occurrence, "FeatureType": featureType, "ElType": elType}
        
        return map
    
    def getElement(self, obj, hash):
        map = json.loads(obj.ElementMap)

        if hash in map:
            element = map[hash]["Element"]
            elementArray = element.split(".")
            subFeatureName = elementArray[0]
            elementName = elementArray[1]
            subFeature = obj.Document.getObject(subFeatureName)
        else:
            raise Exception("Hash: " + str(hash) + " cannot be found in " + obj.Label)
        
        return subFeature, elementName
        
    def generateShape(self, obj, prevShape):
        if obj.Support.TypeId == "Sketcher::SketchObject":
            sketch = obj.Support

            if hasattr(sketch, "Support"):
                container = self.getContainer(obj)

                positionSketch(sketch, container)

            sketch.recompute()

            sketchWires = list(filter(lambda w: w.isClosed(), sketch.Shape.Wires))
            face = Part.makeFace(sketchWires)

            normal = sketch.Placement.Rotation.multVec(App.Vector(0, 0, 1))
            extrudeVector = normal.multiply(obj.Length)

            extrusion = face.extrude(extrudeVector)

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
                    geoType = "Vertex"

                    startPoint = App.Vector(geo.X, geo.Y, geo.Z)
                    endPoint = startPoint + App.Vector(0, 0, obj.Length)
                    
                    if startPoint not in vertexList and endPoint not in vertexList:
                        line = Part.LineSegment(startPoint, endPoint).toShape()
                        obj.WiresDatum.Shape = Part.Compound([obj.WiresDatum.Shape, line])

                        wiresEdgeIndex += 1

                        element = (obj.WiresDatum, "Edge" + str(wiresEdgeIndex))
                        elementMap = self.updateElement(element, geoFacade.Id, elementMap, geoType, 0, "WiresDatum")
                    
                    vertexList.append(startPoint)
                    vertexList.append(endPoint)
                elif isinstance(geo, Part.LineSegment) or isinstance(geo, Part.ArcOfCircle):
                    geoType = "Edge"

                    for i, point in enumerate([geo.StartPoint, geo.EndPoint]):
                        startPoint = point
                        endPoint = point + App.Vector(0, 0, obj.Length)
                        
                        if startPoint not in vertexList and endPoint not in vertexList:
                            line = Part.LineSegment(startPoint, endPoint).toShape()
                        
                            obj.WiresDatum.Shape = Part.Compound([obj.WiresDatum.Shape, line])
                            wiresEdgeIndex += 1
                            wiresVertexIndex += 2

                            element = (obj.WiresDatum, "Edge" + str(wiresEdgeIndex))
                            elementMap = self.updateElement(element, geoFacade.Id, elementMap, geoType, i, "WiresDatum")

                            element = (obj.WiresDatum, "Vertex" + str(wiresVertexIndex))
                            elementMap = self.updateElement(element, geoFacade.Id, elementMap, "Vertex", i, "WiresDatum")

                            element = (obj.WiresDatum, "Vertex" + str(wiresVertexIndex))
                            elementMap = self.updateElement(element, geoFacade.Id, elementMap, "Vertex", i, "WiresDatum")

                        vertexList.append(startPoint)
                        vertexList.append(endPoint)
                
                if type(geo.toShape()).__name__ == "Edge":
                    sketchIndexEdges += 1
                elif type(geo.toShape()).__name__ == "Vertex":
                    sketchIndexVertices += 1
                                
                #Handle SketchProj
                
                geoShape = geo.toShape()
                #geoShape.Placement.Base = vector
                
                # implement hashes for vertices of lines and arcs
                if geoType == "Edge":
                    projElement = (obj.SketchProjection, geoType + str(sketchIndexEdges))
                    element = (obj.Support, geoType + str(sketchIndexEdges))
                else:
                    projElement = (obj.SketchProjection, geoType + str(sketchIndexVertices))
                    element = (obj.Support, geoType + str(sketchIndexVertices))
                
                print("ProjElement: " + projElement[0].Label + "." + projElement[1])
                print("Element: " + element[0].Label + "." + element[1])

                obj.SketchProjection.Shape = Part.Compound([obj.SketchProjection.Shape, geoShape])

                elementMap = self.updateElement(projElement, geoFacade.Id, elementMap, geoType, 0, "SketchProj")
                elementMap = self.updateElement(element, geoFacade.Id, elementMap, geoType, 0, "Sketch")
            
            App.Console.PrintLog(obj.Label + " update datums time: " + str(time.time() - startTime) + "\n")
            
            for hash, value in elementMap.copy().items():
                if int(value["GeoId"]) not in idList:
                    elementMap.pop(hash)

            obj.ElementMap = json.dumps(elementMap)
            
            obj.WiresDatum.Placement = sketch.Placement
            obj.SketchProjection.Placement.Base = sketch.Placement.Base + extrudeVector
            obj.SketchProjection.Placement.Rotation = sketch.Placement.Rotation

            obj.ViewObject.LineWidth = 1
            obj.WiresDatum.ViewObject.LineWidth = 2
            obj.Support.ViewObject.LineWidth = 2
            obj.SketchProjection.ViewObject.LineWidth = 2

            obj.Support.purgeTouched()
            obj.WiresDatum.purgeTouched()
            obj.SketchProjection.purgeTouched()
            
            obj.WiresDatum.Visibility = True
            obj.SketchProjection.Visibility = True
            obj.Support.Visibility = True

            return extrusion

    def execute(self, obj):
        if obj.Group == []:
            obj.Group = [obj.Support, obj.SketchProjection, obj.WiresDatum]

        self.updateProps(obj)
            
    def onChanged(self, obj, prop):
        if prop == "Length":
            obj.touch()

        if prop == "Visibility" and obj.Visibility == True:
            container = self.getContainer(obj)

            if container != None:
                container.Proxy.setShownObj(container, obj)
            else:
                App.Console.PrintWarning("No container found in onChanged!")
            
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

    if hasattr(activeObject, "Type") and activeObject.Type == "PartContainer":
        selectedObject = Gui.Selection.getSelection()

        if len(selectedObject) == 0:
            selectedObject = None
        else:
            selectedObject = selectedObject[0]

        if selectedObject != None and selectedObject.TypeId == "Sketcher::SketchObject":
            obj = App.ActiveDocument.addObject("Part::FeaturePython", "Extrusion")
            wiresDatum = App.ActiveDocument.addObject("Part::Feature", "WiresDatum")
            wiresDatum.addProperty("App::PropertyString", "Type")
            wiresDatum.Type = "WiresDatum"

            sketchProjection = App.ActiveDocument.addObject("Part::Feature", "SketchProjection")
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

            activeObject.Proxy.addObject(activeObject, obj, True)
            activeObject.Proxy.setTip(activeObject, obj)
            obj.Proxy.setSupport(obj, selectedObject)
            obj.Proxy.setDatums(obj, wiresDatum, sketchProjection)
        else:
            App.Console.PrintError("Selected object is not a sketch!\n")
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")