import FreeCAD as App
import FreeCADGui as Gui
import Part
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from Utils import isType, getParent, featureTypes, boundaryTypes
from Entities.Entity import Entity

class ExposedGeo(Entity):
    def __init__(self, obj):
        obj.Proxy = self
        self.updateProps(obj)

    def updateProps(self, obj):
        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "ExposedGeometry"
        
        if not hasattr(obj, "Support"):
            obj.addProperty("App::PropertyString", "Support", "ConstraintDesign", "Element to expose.")
    
    def generateEquations(self):
        pass

    def generateParameters(self):
        pass

    def getConstrainedElements(self):
        pass

    def getContainer(self, obj):
        return super(ExposedGeo, self).getContainer(obj)
        
    def generateShape(self, obj, prevShape):
        print(obj.Label)

        shape = Part.Shape()
        container = self.getContainer(obj)
        elementName = None

        feature, elementName = container.Proxy.getElement(container, obj.Support)
        
        if elementName != None:
            element = feature.Shape.getElement(elementName)
            if element != None:
                shape = Part.Shape(Part.Compound([element]))
                obj.Shape = shape
        
        obj.ViewObject.Selectable = True
        obj.ViewObject.LineWidth = 4 
        
        return shape
    
    # Format {"HashName": {"Edge:" edge, "GeoTag", sketchGeoTag}}

    def getElement(self, obj, hash):
        return None, None

    def getBoundaries(self, obj, isShape=False):
        return []

    def execute(self, obj):
        self.updateProps(obj)
            
    def onChanged(self, obj, prop):
        pass
    
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

class ViewProviderExposedGeo:
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
        self.Object.Selectable = True

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
    
def makeExposedGeo(edges):
    activeObject = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")

    if activeObject != None and hasattr(activeObject, "Type") and activeObject.Type == "PartContainer":
        doc = activeObject.Document
        doc.openTransaction("CreateExposedGeo")

        obj = App.ActiveDocument.addObject("Part::FeaturePython", "ExposedGeo")
        ExposedGeo(obj)
        ViewProviderExposedGeo(obj.ViewObject)

        hashes = []
        afterFeature = edges[0][0]

        if isType(afterFeature, boundaryTypes) or hasattr(afterFeature, "TypeId") and afterFeature.TypeId == "Sketcher::SketchObject":
            afterFeature = getParent(afterFeature, featureTypes)
        elif isType(afterFeature, featureTypes):
            pass
        else:
            afterFeature = None

        print(afterFeature.Name)

        obj.Support = activeObject.Proxy.getHash(activeObject, edges[0], True)
        activeObject.Proxy.addObject(activeObject, obj, False, afterFeature)

        print(edges)
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")