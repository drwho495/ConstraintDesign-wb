import FreeCAD as App
import FreeCADGui as Gui
import Part
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from SolverSystem.SolvableEntity import SolvableEntity

class Fillet(SolvableEntity):
    def __init__(self, obj):
        obj.Proxy = self

        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "Fillet"

        if not hasattr(obj, "Radius"):
            obj.addProperty("App::PropertyFloat", "Radius", "ConstraintDesign", "Internal storage for radius of fillet. Updated every solve.")
            obj.Radius = 1.0
        
        if not hasattr(obj, "Edges"):
            obj.addProperty("App::PropertyXLinkSubList", "Edges", "ConstraintDesign", "Edges to fillet.")
    
    def generateEquations(self):
        pass

    def generateParameters(self):
        pass

    def getConstrainedElements(self):
        pass

    def getContainer(self, obj):
        obj = obj.InList[0]

        if hasattr(obj, "Type") and obj.Type == "PartContainer":
            return obj
        else:
            return None
        
    def generateShape(self, obj, prevShape):
        if prevShape.isNull():
            raise Exception("No feature before this fillet!")

        datumEdges = obj.Edges
        allShapeEdges = prevShape.Edges
        edgesToFillet = []
        
        for edge in allShapeEdges:
            length = edge.Length
            
            for datumEdge in datumEdges:
                feature = datumEdge[0]

                print(datumEdge)
                datumTypes = ["WiresDatum", "SketchProjection"]

                if (hasattr(feature, "Type") and feature.Type in datumTypes) or feature.TypeId == "Sketcher::SketchObject":
                    for internalDatumEdge in datumEdge[1]:
                        internalDatumEdge = feature.Shape.getElement(internalDatumEdge)

                        if (
                            edge.CenterOfMass.isEqual(internalDatumEdge.CenterOfMass, 1e-2) or
                            (len(edge.Curve.intersectCC(internalDatumEdge.Curve)) > 1 and edge.Curve.TypeId == internalDatumEdge.Curve.TypeId)
                            # edge.Placement.isSame(internalDatumEdge.Placement, 1e-2)
                        ):
                            edgesToFillet.append(edge)
                        else:
                            print(feature.Label)
                else:
                    print(feature.Label)
                    print("Incorrect feature type.")
        
        filletShape = prevShape.makeFillet(obj.Radius, edgesToFillet)
        obj.Shape = filletShape

        return filletShape

    def execute(self, obj):
        pass
            
    def onChanged(self, obj, prop):
        pass
            
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

class ViewProviderFillet:
    def __init__(self, obj):
        obj.Proxy = self
        obj.Selectable = False
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
        return []

    def dragObject(self, obj):
        App.Console.PrintMessage(obj)

    def __getstate__(self):
        # Called when saving
        return None

    def __setstate__(self, state):
        # Called when restoring
        return None
    
def makeFillet(edges):
    activeObject = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")

    if hasattr(activeObject, "Type") and activeObject.Type == "PartContainer":
        obj = App.ActiveDocument.addObject("Part::FeaturePython", "Fillet")
        Fillet(obj)
        ViewProviderFillet(obj.ViewObject)

        activeObject.Proxy.addObject(activeObject, obj)
        activeObject.Proxy.setTip(activeObject, obj)

        obj.Edges = edges
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")