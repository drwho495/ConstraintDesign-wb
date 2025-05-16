import FreeCAD as App
import FreeCADGui as Gui
import Part
from Entities.ConstraintGroup import makeConstraintGroup

class PartContainer:
    def updateProps(self, obj):
        if not hasattr(obj, "Group"):
            obj.addProperty("App::PropertyLinkList", "Group", "Base", "List of contained objects.")
        
        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "PartContainer"
        
        if not hasattr(obj, "Origin"):
            obj.addProperty("App::PropertyXLink", "Origin", "ConstraintDesign", "Name of the origin object.")
        
        if not hasattr(obj, "Tip"):
            obj.addProperty("App::PropertyXLink", "Tip", "ConstraintDesign", "The tip feature of the container.")

        if not hasattr(obj, "ConstraintGroup"):
            obj.addProperty("App::PropertyXLink", "ConstraintGroup", "ConstraintDesign", "Constraint group object.")

    def __init__(self, obj):
        obj.Proxy = self

        self.updateProps(obj)
        
    def addObject(self, obj, objToAdd):
        group = obj.Group
        group.append(objToAdd)

        obj.Group = group
    
    def setTip(self, part, feature):
        if not hasattr(part, "Tip"):
            self.updateProps(part)

        part.Tip = feature
    
    def addGroup(self, obj, group):
        obj.ConstraintGroup = group

        self.addObject(obj, group)
    
    def recalculateShapes(self, obj):
        prevShape = Part.Shape()

        if not hasattr(obj, "Tip"):
            self.updateProps(obj)

        featureTypes = ["Extrusion", "Fillet"]

        for child in obj.Group:
            if hasattr(child, "Type") and child.Type in featureTypes:
                prevShape = child.Proxy.generateShape(child, prevShape)

                if child != obj.Tip:
                    child.Visibility = False
                else:
                    child.Visibility = True

                child.purgeTouched()
    
    def addOrigin(self, obj, origin):
        obj.Origin = origin

        self.addObject(obj, origin)
        
    def execute(self, obj):
        self.recalculateShapes(obj)
            
    def onChanged(self, obj, prop):
        pass
            
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

class ViewProviderPartContainer:
    def __init__(self, obj):
        obj.Proxy = self
        self.Editable = True
    
    def onDelete(self, vobj, subelements): # TODO: Check for constraint design elements
        if hasattr(vobj.Object, "Origin"):
            if vobj.Object.Origin != None:
                vobj.Object.Document.removeObject(vobj.Object.Origin.Name)

        if hasattr(vobj.Object, "ConstraintGroup"):
            if vobj.Object.ConstraintGroup != None:
                vobj.Object.ConstraintGroup.Proxy.deleteConstraints(vobj.Object.ConstraintGroup)
                vobj.Object.Document.removeObject(vobj.Object.ConstraintGroup.Name)
        
        # feature.Document.removeObject(feature.Name)
        return True

    def setEdit(self, vobj, mode):
        if Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign") != vobj.Object:
            Gui.ActiveDocument.ActiveView.setActiveObject("ConstraintDesign", vobj.Object)
            return True
        else:
            Gui.ActiveDocument.ActiveView.setActiveObject("ConstraintDesign", None)
            return False

    def unsetEdit(self, vobj, mode):
        App.Console.PrintMessage("Leaving edit mode\n")
        Gui.ActiveDocument.ActiveView.setActiveObject(vobj.Object.Name, None)
        return True


    def attach(self, vobj):
        # Called when the view provider is attached
        self.Object = vobj

        return

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
        # Return a custom icon (optional)
        return """
            /* XPM */
            static const char *icon[] = {
            "16 16 2 1",
            "  c None",
            ". c #0000FF",
            "                ",
            "       ..       ",
            "      ....      ",
            "     ......     ",
            "    ........    ",
            "   ..........   ",
            "  ............  ",
            " .............. ",
            " .............. ",
            "  ............  ",
            "   ..........   ",
            "    ........    ",
            "     ......     ",
            "      ....      ",
            "       ..       ",
            "                "
            };
        """
    
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
    
def makePartContainer():
    obj = App.ActiveDocument.addObject("Part::FeaturePython", "PartContainer")
    origin = App.ActiveDocument.addObject("App::Origin", "Origin")
    group = makeConstraintGroup()

    part = PartContainer(obj)
    viewProvider = ViewProviderPartContainer(obj.ViewObject)

    part.addOrigin(obj, origin)
    part.addGroup(obj, group)
    return obj