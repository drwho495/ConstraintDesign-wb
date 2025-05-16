import FreeCAD as App
import FreeCADGui as Gui
import Part

class GuiConstraint:
    def __init__(self, obj):
        obj.Proxy = self

        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "Constraint"
        
        if not hasattr(obj, "ConstraintType"):
            obj.addProperty("App::PropertyString", "ConstraintType", "ConstraintDesign", "Type of constraint.")

        if not hasattr(obj, "Element1"):
            obj.addProperty("App::PropertyXLink", "Element1", "ConstraintDesign", "First element of constraint.")

        if not hasattr(obj, "Element2"):
            obj.addProperty("App::PropertyXLink", "Element2", "ConstraintDesign", "Second element of constraint.")

    def updateElements(self, obj, elements):
        obj.Element1 = elements[0]
        obj.Element2 = elements[1]
    
    def execute(self, obj):
        pass
            
    def onChanged(self, obj, prop):
        pass
            
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

class ViewProviderGuiConstraint:
    def __init__(self, obj):
        obj.Proxy = self
        self.Editable = True
    
    def onDelete(self, vobj, subelements): # TODO: Check for constraint design elements
        return True

    def attach(self, vobj):
        # Called when the view provider is attached
        self.Object = vobj

        return
    
    def dragObject(self, obj):
        return False

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
    
    def __getstate__(self):
        # Called when saving
        return None

    def __setstate__(self, state):
        # Called when restoring
        return None
    
def makeGuiConstraint(name, elements):
    activeObject = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")

    if activeObject != None and activeObject.Type == "PartContainer":
        constraint = App.ActiveDocument.addObject("App::FeaturePython", name)

        activeObject.ConstraintGroup.addObject(constraint)

        part = GuiConstraint(constraint)
        part.ConstraintType = name

        viewProvider = ViewProviderGuiConstraint(constraint.ViewObject)

        constraint.Proxy.updateElements(constraint, elements)

        return constraint
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")
        return None