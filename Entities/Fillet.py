import FreeCAD as App
import FreeCADGui as Gui
import Part
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from Entities.Entity import SolvableEntity

class Fillet(SolvableEntity):
    def __init__(self, obj):
        obj.Proxy = self
        self.updateProps(obj)

    def updateProps(self, obj):
        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "Fillet"

        if not hasattr(obj, "Radius"):
            obj.addProperty("App::PropertyFloat", "Radius", "ConstraintDesign", "Internal storage for radius of fillet. Updated every solve.")
            obj.Radius = 1.0
        
        if not hasattr(obj, "Edges"):
            obj.addProperty("App::PropertyStringList", "Edges", "ConstraintDesign", "Edges to fillet.")
    
    def generateEquations(self):
        pass

    def generateParameters(self):
        pass

    def getConstrainedElements(self):
        pass

    def getContainer(self, obj):
        return super(Fillet, self).getContainer(obj)
        
    def generateShape(self, obj, prevShape):
        if prevShape.isNull():
            raise Exception("No feature before this fillet!")

        datumEdges = obj.Edges
        allShapeEdges = prevShape.Edges
        edgesToFillet = []
        container = self.getContainer(obj)

        if container == None:
            App.Console.PrintError(obj.Label + " is unable to find parent container!")

            return prevShape
        else:
            for edge in allShapeEdges:
                for datumEdge in datumEdges:
                    try:
                        feature, datumEdge = container.Proxy.getElement(container, datumEdge)
                    except Exception as e:
                        App.Console.PrintError(str(e))
                        continue
                    
                    datumEdge = feature.Shape.getElement(datumEdge)

                    intersectionPoints = 0

                    try:
                        intersectionPoints = len(edge.Curve.intersectCC(datumEdge.Curve))
                    except:
                        intersectionPoints = -1

                    if (
                        edge.CenterOfMass.isEqual(datumEdge.CenterOfMass, 1e-2) or
                        ((intersectionPoints > 2 or intersectionPoints == -1) and edge.Curve.TypeId == datumEdge.Curve.TypeId)
                        # edge.Placement.isSame(internalDatumEdge.Placement, 1e-2)
                    ):
                        edgesToFillet.append(edge)
                    else:
                        print(feature.Label)
            try:
                filletShape = prevShape.makeFillet(obj.Radius, edgesToFillet)
            except:
                filletShape = prevShape
                App.Console.PrintError(obj.Label + ": creating a fillet with the radius of " + str(obj.Radius) + " failed!\n")
                App.Console.PrintMessage("The number of edges in this operation is: " + str(len(edgesToFillet)) + "\n")
            
            obj.Shape = filletShape

            return filletShape
    
    # Format {"HashName": {"Edge:" edge, "GeoTag", sketchGeoTag}}

    def getElement(self, obj, hash):
        return None, None

    def execute(self, obj):
        self.updateProps(obj)
            
    def onChanged(self, obj, prop):
        if prop == "Radius":
            obj.touch()
        
        if prop == "Visibility" and obj.Visibility == True:
            container = self.getContainer(obj)

            container.Proxy.setShownObj(container, obj)
            
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

        hashes = []

        activeObject.Proxy.addObject(activeObject, obj, True)
        activeObject.Proxy.setTip(activeObject, obj)
        for edge in edges:
            hashes.append(activeObject.Proxy.getHash(activeObject, edge, True))

        obj.Edges = hashes
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")