import FreeCAD as App
import FreeCADGui as Gui
import Part

class ConstraintGroup:
    def __init__(self, obj):
        obj.Proxy = self
    
    def execute(self, obj):
        pass
            
    def onChanged(self, obj, prop):
        pass
            
    def __getstate__(self):
        return None

    def deleteConstraints(self, object):
        for obj in object.Group:
            object.Document.removeObject(obj.Name)

    def __setstate__(self, state):
        return None

class ViewProviderConstraintGroup:
    def __init__(self, obj):
        obj.Proxy = self
    
    def onDelete(self, vobj, subelements): # TODO: Check for constraint design elements
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
    
    def claimChildren(self):
        # App.Console.PrintMessage('claimChildren called\n')
        for obj in self.Object.Object.Group:
            if not hasattr(obj, "Type") or obj.Type != "Constraint":
                self.Object.Object.removeObject(obj)

                # group = self.Object.Group
                # group.remove(obj)
                # self.Object.Group = group
        
        return self.Object.Object.Group

    def dragObject(self, obj):
        App.Console.PrintMessage(obj)

    def __getstate__(self):
        # Called when saving
        return None

    def __setstate__(self, state):
        # Called when restoring
        return None
    
def makeConstraintGroup():
    obj = App.ActiveDocument.addObject("App::DocumentObjectGroupPython", "ConstraintGroup")

    group = ConstraintGroup(obj)
    viewProvider = ViewProviderConstraintGroup(obj.ViewObject)

    return obj