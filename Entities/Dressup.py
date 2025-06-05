import FreeCAD as App
import FreeCADGui as Gui
import Part
import sys
import math
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from Entities.Entity import Entity

# 0 for Fillet
# 1 for Chamfer
# 2 for Countersink

class FeatureDressup(Entity):
    def __init__(self, obj, dressupType):
        obj.Proxy = self
        self.updateProps(obj, dressupType)

    def updateProps(self, obj, dressupType = 0):
        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "Fillet"
        
        if not hasattr(obj, "DressupType"):
            obj.addProperty("App::PropertyInteger", "DressupType", "ConstraintDesign", "Type of feature dressup.\n0 for fillet\n1 for chamfer")
            obj.DressupType = dressupType
            obj.setEditorMode("DressupType", 3)
        
        if not hasattr(obj, "Suppressed"):
            obj.addProperty("App::PropertyBool", "Suppressed", "ConstraintDesign", "Is feature used.")
            obj.Suppressed = False

        if hasattr(obj, "DressupType") and obj.DressupType == 0:
            if not hasattr(obj, "Radius"):
                obj.addProperty("App::PropertyFloat", "Radius", "ConstraintDesign", "Radius of fillet.")
                obj.Radius = 1.0
        elif hasattr(obj, "DressupType") and obj.DressupType == 1:
            if not hasattr(obj, "Length"):
                obj.addProperty("App::PropertyFloat", "Length", "ConstraintDesign", "Length of fillet.")
                obj.Length = 1.0
        elif hasattr(obj, "DressupType") and obj.DressupType == 2:
            if not hasattr(obj, "Diameter"):
                obj.addProperty("App::PropertyFloat", "Diameter", "ConstraintDesign", "Diameter of the countersink.")
                obj.Diameter = 8
            if not hasattr(obj, "Angle"):
                obj.addProperty("App::PropertyFloat", "Angle", "ConstraintDesign", "Angle of the countersink in degrees.")
                obj.Angle = 90
        
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
        
    def generateShape(self, obj, prevShape):
        if prevShape.isNull():
            raise Exception("No feature before this fillet!")

        datumEdges = obj.Edges
        allShapeEdges = prevShape.Edges
        elementsToDressup = []
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
                        elementsToDressup.append(edge)
                dressupShape = prevShape

            if hasattr(obj, "DressupType") and obj.DressupType == 0:
                try:
                    dressupShape = prevShape.makeFillet(obj.Radius, elementsToDressup)
                except Exception as e:
                    dressupShape = prevShape
                    App.Console.PrintError(obj.Label + ": creating a fillet with the radius of " + str(obj.Radius) + " failed!\nException: " + str(e) + "\n")
            elif hasattr(obj, "DressupType") and obj.DressupType == 1:
                try:
                    dressupShape = prevShape.makeChamfer(obj.Length, elementsToDressup)
                except Exception as e:
                    dressupShape = prevShape
                    App.Console.PrintError(obj.Label + ": creating a chamfer with the length of " + str(obj.Length) + " failed!\nException: " + str(e) + "\n")
            elif hasattr(obj, "DressupType") and obj.DressupType == 2:
                try:
                    depth = obj.Diameter/2 * math.tan((math.radians(obj.Angle)) / 2)
                    cone = Part.makeCone(obj.Diameter/2, 0, depth, App.Vector(0,0,0), App.Vector(0,0,-1), 360)
                    cutCompound = []

                    for edge in elementsToDressup:
                        print("countersink")

                        if edge.Curve.TypeId == "Part::GeomCircle":
                            placement = App.Placement()
                            placement.Base = edge.CenterOfMass
                            placement.Rotation = edge.Placement.Rotation
                            
                            cone.Placement = placement
                            cutCompound.append(cone.copy())
                        else:
                            print("edge is not a circle")
                    
                    dressupShape = prevShape.cut(Part.Compound(cutCompound))
                except Exception as e:
                    dressupShape = prevShape
                    App.Console.PrintError(obj.Label + ": creating a countersink failed!\nException: " + str(e) + "\n")
            
            obj.Shape = dressupShape

            return dressupShape
    
    # Format {"HashName": {"Edge:" edge, "GeoTag", sketchGeoTag}}

    def getElement(self, obj, hash):
        return None, None

    def getBoundaries(self, obj, isShape=False):
        return []

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

""" Method to create a FeatureDressup. """
def makeDressup(edges, type):
    activeObject = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")

    if activeObject != None and hasattr(activeObject, "Type") and activeObject.Type == "PartContainer":
        name = "Dressup"
        doc = activeObject.Document
        doc.openTransaction("CreateDressup")

        if type == 0:
            name = "Fillet"
        elif type == 1:
            name = "Chamfer"
        elif type == 2:
            name = "Countersink"

        obj = App.ActiveDocument.addObject("Part::FeaturePython", name)
        FeatureDressup(obj, type)
        ViewProviderDressup(obj.ViewObject)

        hashes = []

        activeObject.Proxy.addObject(activeObject, obj, True)
        activeObject.Proxy.setTip(activeObject, obj)

        print(edges)

        for edge in edges:
            # print(edge)

            hashes.append(activeObject.Proxy.getHash(activeObject, edge, True))

        obj.Edges = hashes
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")