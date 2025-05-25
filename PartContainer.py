import FreeCAD as App
import FreeCADGui as Gui
import Part
import time
import os
import json
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
        
        if not hasattr(obj, "ShownFeature"):
            obj.addProperty("App::PropertyXLink", "ShownFeature", "ConstraintDesign", "The feature that is being shown.")

    def __init__(self, obj):
        obj.Proxy = self

        self.updateProps(obj)
        
    def addObject(self, obj, objToAdd, isFeature=False):
        group = obj.Group
        if isFeature and obj.Tip != None:
            index = group.index(obj.Tip)

            group.insert(index + 1, objToAdd)
        else:
            group.append(objToAdd)

        obj.Group = group
    
    def setTip(self, obj, feature):
        if not hasattr(obj, "Tip"):
            self.updateProps(obj)

        obj.Tip = feature
        obj.ShownFeature = obj.Tip # Make setting in pref?

    def setShownObj(self, obj, feature):
        obj.ShownFeature = feature
        group = self.getGroup(obj)
        group.remove(feature)

        for item in group: item.Visibility = False

    def addGroup(self, obj, group):
        obj.ConstraintGroup = group

        self.addObject(obj, group)
    
    def getGroup(self, obj):
        ls = []
        featureTypes = ["Extrusion", "Fillet"]

        for item in obj.Group:
            if hasattr(item, "Type") and item.Type in featureTypes:
                ls.append(item)
        
        return ls
    
    def fixTip(self, obj, group=None):
        if not obj.Tip in obj.Group:
            if group == None:
                group = self.getGroup(obj)
            
            if len(group) > 0:
                obj.Tip = group[len(group) - 1]
            #obj.Tip.Visibility = True
    
    def recalculateShapes(self, obj, startObj = None):
        prevShape = Part.Shape()
        startTime = time.time()

        if not hasattr(obj, "Tip"):
            self.updateProps(obj)

        tipFound = False
        group = self.getGroup(obj)
        startIndex = 0

        if startObj != None and startObj in group:
            startIndex = group.index(startObj)

        for i, child in enumerate(group):
            if i >= startIndex:
                newShape = child.Proxy.generateShape(child, prevShape)

                if not newShape.isNull():
                    prevShape = newShape
            else:
                newShape = child.Shape

                if not newShape.isNull():
                    prevShape = newShape
            
            if obj.ShownFeature != child:
                child.Visibility = False # only set to false to avoid recursion

            if child == obj.Tip:
                tipFound = True

            child.purgeTouched()
        
        if not tipFound:
            self.fixTip(obj, group)
        
        if obj.ShownFeature == None and obj.Tip != None:
            obj.ShownFeature = obj.Tip
            obj.ShownFeature.Visibility = True

        App.Console.PrintLog("Time to recompute: " + str(time.time() - startTime))
    
    def addOrigin(self, obj, origin):
        obj.Origin = origin

        self.addObject(obj, origin)
        
    def execute(self, obj):
        self.updateProps(obj)
        self.recalculateShapes(obj)
    
    def getFullGroup(self, obj):
        group = obj.Group

        for item in obj.Group:
            if hasattr(item, "Group"):
                group.extend(item.Group)
        
        return group
            
    def onChanged(self, obj, prop):
        if prop == "Placement":
            group = self.getFullGroup(obj)

            for item in group:
                if hasattr(item, "Placement"):
                    # item.Placement = obj.Placement
                    item.purgeTouched()
            obj.purgeTouched()
    
    def getHash(self, obj, element, full=False):
        feature = element[0]
        elementName = element[1]
        parent = feature.InList[0]

        if hasattr(parent, "Type") and parent.Type == "Extrusion":
            if hasattr(parent, "ElementMap"):
                map = json.loads(parent.ElementMap)

                for hash, value in map.items():
                    print(feature.Name + "." + elementName)
                    print(value["Element"])

                    if value["Element"] == feature.Name + "." + elementName:
                        if full == False:
                            return hash
                        else:
                            return parent.Name + "." + hash
            else:
                print("no map")
        else:
            print("incorrect type")
    
    def getElement(self, obj, element):
        elementArray = element.split(".")

        if len(elementArray) != 2:
            App.Console.PrintError("Malformed element reference!\nPlease remove any periods in your feature names\n(If one somehow does contain a period, then you will need to recreate it)\n")
        else:
            featureName = elementArray[0]
            hash = elementArray[1]
            featureGroup = self.getFullGroup(obj)
            featureInGroup = None

            for feature in featureGroup:
                if feature.Name == featureName:
                    featureInGroup = feature
            
            if featureInGroup == None:
                App.Console.PrintError("Feature in element reference not found!\n")
            else:
                try:
                    return featureInGroup.Proxy.getElement(featureInGroup, hash)
                except Exception as e:
                    raise e

    # This is for debugging
    def highlightElement(self, obj, element):
        feature, element = self.getElement(obj, element)

        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(feature, [element])
            
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
        
        print("delete: pc")
        
        # feature.Document.removeObject(feature.Name)
        return True

    def setEdit(self, vobj, mode):
        if Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign") != vobj.Object:
            Gui.ActiveDocument.ActiveView.setActiveObject("ConstraintDesign", vobj.Object)
            return False
        else:
            Gui.ActiveDocument.ActiveView.setActiveObject("ConstraintDesign", None)
            return False

    def unsetEdit(self, vobj, mode):
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
        return os.path.join(os.path.dirname(__file__), "icons", "ConstraintPart.svg")
    
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