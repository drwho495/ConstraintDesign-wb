import FreeCAD as App
import FreeCADGui as Gui
import Part
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from SolverSystem.SolvableEntity import SolvableEntity

class Extrusion(SolvableEntity):
    def __init__(self, obj):
        obj.Proxy = self

        if not hasattr(obj, "WiresDatum"):
            obj.addProperty("App::PropertyXLink", "WiresDatum", "ConstraintDesign")
            obj.setEditorMode("WiresDatum", 3)
        
        if not hasattr(obj, "SketchProjection"):
            obj.addProperty("App::PropertyXLink", "SketchProjection", "ConstraintDesign")
            obj.setEditorMode("SketchProjection", 3)
        
        if not hasattr(obj, "Support"):
            obj.addProperty("App::PropertyXLink", "Support", "ConstraintDesign", "Support object (ex: A sketch)")
        
        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "Extrusion"

        if not hasattr(obj, "Remove"):
            obj.addProperty("App::PropertyBool", "Remove", "ConstraintDesign", "Determines the type of boolean operation to perform.")
            obj.Remove = False
        
        if not hasattr(obj, "Group"):
            obj.addProperty("App::PropertyLinkList", "Group", "ConstraintDesign", "Group")
        
        if not hasattr(obj, "Length"):
            obj.addProperty("App::PropertyFloat", "Length", "ConstraintDesign", "Internal storage for length of extrusion. Updated every solve.")
            obj.Length = 10
    
    def generateEquations(self):
        pass

    def generateParameters(self):
        pass

    def getConstrainedElements(self):
        pass

    def setDatums(self, obj, wiresDatum, sketchProjection):
        obj.WiresDatum = wiresDatum
        obj.SketchProjection = sketchProjection
        
    def setSupport(self, obj, support):
        obj.Support = support
    
    def getContainer(self, obj):
        obj = obj.InList[0]

        if hasattr(obj, "Type") and obj.Type == "PartContainer":
            return obj
        else:
            return None
        
    def generateShape(self, obj, prevShape):
        if obj.Support.TypeId == "Sketcher::SketchObject":
            sketch = obj.Support
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
            vertexList = []

            for geo in sketch.Geometry:
                line = Part.Shape()
                
                # Handle Wires
                if len(vertexList) == 0:
                    startPoint = sketch.Shape.CenterOfGravity
                    endPoint = startPoint + App.Vector(0, 0, obj.Length)
                    
                    #wires.Shape = Part.Compound([wires.Shape, Part.LineSegment(startPoint, endPoint).toShape()])
                
                if isinstance(geo, Part.Point):
                    startPoint = App.Vector(geo.X, geo.Y, geo.Z)
                    endPoint = startPoint + App.Vector(0, 0, obj.Length)
                    
                    print(startPoint)
                    print(endPoint)
                    
                    if startPoint in vertexList or endPoint in vertexList:
                        continue
                    
                    line = Part.LineSegment(startPoint, endPoint).toShape()
                    obj.WiresDatum.Shape = Part.Compound([obj.WiresDatum.Shape, line])
                elif isinstance(geo, Part.LineSegment) or isinstance(geo, Part.ArcOfCircle):
                    for point in [geo.StartPoint, geo.EndPoint]:
                        startPoint = point
                        endPoint = point + App.Vector(0, 0, obj.Length)
                        
                        if startPoint in vertexList or endPoint in vertexList:
                            continue
                        
                        line = Part.LineSegment(startPoint, endPoint).toShape()
                    
                        obj.WiresDatum.Shape = Part.Compound([obj.WiresDatum.Shape, line])
                
                #Handle SketchProj
                
                geoShape = geo.toShape()
                #geoShape.Placement.Base = vector
                
                # maybe add the whole list here?
                obj.SketchProjection.Shape = Part.Compound([obj.SketchProjection.Shape, geoShape])
            
            obj.WiresDatum.Placement = sketch.Placement
            obj.SketchProjection.Placement.Base = sketch.Placement.Base + extrudeVector
            obj.SketchProjection.Placement.Rotation = sketch.Placement.Rotation

            obj.WiresDatum.ViewObject.LineWidth = 4
            obj.Support.ViewObject.LineWidth = 4
            obj.SketchProjection.ViewObject.LineWidth = 4

            obj.Support.purgeTouched()
            obj.WiresDatum.purgeTouched()
            obj.SketchProjection.purgeTouched()
            
            obj.WiresDatum.Visibility = True
            obj.SketchProjection.Visibility = True
            obj.Support.Visibility = True

            return extrusion

    def execute(self, obj):
        if not hasattr(obj.WiresDatum, "Type"):
            obj.WiresDatum.addProperty("App::PropertyString", "Type")
            obj.WiresDatum.Type = "WiresDatum"
        
        if not hasattr(obj.SketchProjection, "Type"):
            obj.SketchProjection.addProperty("App::PropertyString", "Type")
            obj.SketchProjection.Type = "SketchProjection"

        if not hasattr(obj, "Group"):
            obj.addProperty("App::PropertyLinkList", "Group", "ConstraintDesign", "Group")
            obj.Group = [obj.Support, obj.SketchProjection, obj.WiresDatum]
            
    def onChanged(self, obj, prop):
        # if prop == "Visibility" and obj.Visibility == True:
            # container = self.getContainer(obj)

            # print(prop)
            # print(obj.Visibility)

            # if container is not None:
                # if container.Tip != obj:
                    # obj.Visibility = False
        pass
            
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
            vobj.Object.Document.removeObject(vobj.Object.WiresDatum.Name)

        if hasattr(vobj.Object, "SketchProjection"):
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

            part = Extrusion(obj)
            viewProvider = ViewProviderExtrusion(obj.ViewObject)

            activeObject.Proxy.addObject(activeObject, obj)
            activeObject.Proxy.setTip(activeObject, obj)
            obj.Proxy.setSupport(obj, selectedObject)
            obj.Proxy.setDatums(obj, wiresDatum, sketchProjection)
        else:
            App.Console.PrintError("Selected object is not a sketch!\n")
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")