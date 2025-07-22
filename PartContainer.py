import FreeCAD as App
import FreeCADGui as Gui
import Part
import time
import os
from Utils.Utils import isType, getDependencies, getParent, isGearsWBPart, fixGear
from Utils.Constants import *
import json

class PartContainer:
    def updateProps(self, obj):
        if not obj.hasExtension("App::OriginGroupExtensionPython"):
            obj.addExtension("App::OriginGroupExtensionPython")
            
            obj.Origin = App.ActiveDocument.addObject("App::Origin", "Origin")

            if hasattr(obj, "Group"): self.oldGroup = obj.Group

        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "PartContainer"
        
        if not hasattr(obj, "ObjectVisibilityDict"):
            obj.addProperty("App::PropertyString", "ObjectVisibilityDict", "ConstraintDesign", "Type of constraint design feature.")
            obj.setEditorMode("ObjectVisibilityDict", 3)
            obj.ObjectVisibilityDict = "{}"
        
        if not hasattr(obj, "Tip"):
            obj.addProperty("App::PropertyXLink", "Tip", "ConstraintDesign", "The tip feature of the container.")

        if not hasattr(obj, "ShownFeature"):
            obj.addProperty("App::PropertyXLink", "ShownFeature", "ConstraintDesign", "The feature that is being shown.")

    def __init__(self, obj = None):
        if obj is not None:
            obj.Proxy = self

            if hasattr(obj, "Group"): self.oldGroup = obj.Group
            self.updateProps(obj)
    
    def updateSupportVisibility(self, obj, supportObject, updateDict = True):
        if obj.ObjectVisibilityDict != "{}":
            self.resetVisibility(obj)
        
        objectVisibilityDict = {}

        if not hasattr(obj, "ObjectVisibilityDict"):
            self.updateProps(obj)
        
        if isType(supportObject, supportTypes):
            feature = getParent(supportObject, featureTypes)
            group = self.getGroup(obj, True, True)

            if feature != None:
                cutoffIndex = group.index(feature)

                if updateDict:
                    for item in obj.Group:
                        objectVisibilityDict[item.Name] = item.Visibility # has to be run seperately, the visibilities change when they shouldn't sometimes

                for item in group:
                    itemGroup = [item]
                    hide = False

                    if item in supportObject.OutList or isType(supportObject, datumTypes) or item == feature or group.index(item) > cutoffIndex:
                        hide = True

                    if hasattr(item, "Group"):
                        itemGroup.extend(item.Group)
                    
                    for hideItem in itemGroup:
                        hideItem.Visibility = not hide
        
        if updateDict:
            try:
                obj.ObjectVisibilityDict = json.dumps(objectVisibilityDict)
            except:
                obj.ObjectVisibilityDict = "{}"
    
    def resetVisibility(self, obj): # i store and recieve object's visibility like this because the user might want to have a specifc datum hidden/shown
        visibilityList = None

        if not hasattr(obj, "ObjectVisibilityDict"):
            self.updateProps(obj)
        
        try:
            visibilityList = json.loads(obj.ObjectVisibilityDict)
        except:
            pass

        if visibilityList != None:
            for objName, val in visibilityList.items():
                object = obj.Document.getObject(objName) # object object object object

                if object != None and isinstance(val, bool):
                    object.Visibility = val
            obj.ObjectVisibilityDict = "{}"
    
    def attach(self, obj):
        if hasattr(obj, "Group"): self.oldGroup = obj.Group
        self.updateProps(obj)
    
    def addObject(self, obj, objToAdd, afterTip=False, customAfterFeature = None):
        group = obj.Group

        if customAfterFeature == None or (customAfterFeature != None and customAfterFeature not in group):
            if afterTip and obj.Tip != None and obj.Tip in group:
                index = group.index(obj.Tip)
                addIndex = index

                for i, feature in enumerate(group):
                    deps = getDependencies(feature, obj)

                    if len(deps) != 0 and obj.Tip.Name in deps:
                        if i > index: addIndex += 1

                group.insert(addIndex + 1, objToAdd)
            else:
                group.append(objToAdd)
        elif customAfterFeature != None and customAfterFeature in group:
            index = group.index(customAfterFeature)

            group.insert(index + 1, objToAdd)

            
        if hasattr(objToAdd, "Group") and len(objToAdd.Group) != 0:
            group.extend(objToAdd.Group)

        obj.Group = group
    
    def setTip(self, obj, feature):
        if not hasattr(obj, "Tip"):
            self.updateProps(obj)

        obj.Tip = feature
        obj.ShownFeature = obj.Tip # Make setting in pref?

    def setShownObj(self, obj, feature):
        inEdit = Gui.ActiveDocument.getInEdit()

        if inEdit != None and isType(inEdit.Object, "BoundarySketch"):
            return
        
        obj.ShownFeature = feature
        group = self.getGroup(obj, False)
        group.remove(feature)

        for item in group: item.Visibility = False

    def getGroup(self, obj, withNonFeatureEntities = False, skipSketch=False):
        filteredGroup = []
        for item in obj.Group:
            if (hasattr(item, "Type") and item.Type in featureTypes) or (isType(item, "BoundarySketch") and not skipSketch) or (withNonFeatureEntities and isType(item, datumTypes)):
                filteredGroup.append(item)
        
        return filteredGroup

    def getGroupOfTypes(self, obj, type = [], excludeObjectNames = []):
        """
            returns a group of a specific type (or types) of object in an `obj`
            `obj` should be a container
            `type` should be a string or list of strings
            `excludeObjectNames` excludes objects with certain names. Needs to be a list.
        """
        sortedGroup = []

        for item in obj.Group:
            if isType(item, type) and item.Name not in excludeObjectNames:
                sortedGroup.append(item)
        
        return sortedGroup
    
    def fixTip(self, obj):
        if not obj.Tip in obj.Group:
            group = self.getGroup(obj, False, True)
            
            if len(group) > 0:
                obj.Tip = group[len(group) - 1]
            #obj.Tip.Visibility = True

    def recalculateShapes(self, obj, startObj = None):
        prevShape = Part.Shape()
        startTime = time.time()
        inEdit = Gui.ActiveDocument.getInEdit()
        self.updateProps(obj)

        if hasattr(obj, "Group"): self.oldGroup = obj.Group

        if inEdit != None and isType(inEdit.Object, "BoundarySketch"):
            return
        
        if obj.ObjectVisibilityDict != "{}":
            self.resetVisibility(obj)

        tipFound = False
        group = self.getGroup(obj, True)
        startIndex = 0

        recomputedNameList = []

        if startObj != None and startObj in group:
            startIndex = group.index(startObj)

        # handle features
        for i, child in enumerate(group):
            if isType(child, "BoundarySketch"):
                child.Proxy.updateSketch(child, obj)
            elif isType(child, featureTypes):
                if i >= startIndex and not child.Suppressed:
                    if hasattr(child.Proxy, "getSupports"):
                        supports = child.Proxy.getSupports(child)

                        if len(supports) != 0:
                            depList = []
                            
                            for support in supports:
                                depList.extend(support.OutList)

                            for item in depList:
                                if isType(item, datumTypes) and item.Name not in recomputedNameList and hasattr(item.Proxy, "generateShape"):
                                    item.Proxy.generateShape(item, Part.Shape())
                                    recomputedNameList.append(item.Name)

                    startTime2 = time.time()
                    newShape = child.Proxy.generateShape(child, prevShape)
                    App.Console.PrintLog(f"Time to recompute {child.Label}: {str(time.time() - startTime2)}\n")

                    recomputedNameList.append(child.Name)

                    if not newShape.isNull():
                        prevShape = newShape
                else:
                    if hasattr(child, "Shape"):
                        child.Shape = prevShape

                if obj.ShownFeature != child:
                    child.Visibility = False # only set to false to avoid recursion

                if child == obj.Tip:
                    tipFound = True

            child.purgeTouched()

        #handle datums that haven't already been recomputed
        for item in self.getGroupOfTypes(obj, datumTypes, recomputedNameList):
            if hasattr(item.Proxy, "generateShape"):
                item.Proxy.generateShape(item, Part.Shape())
        
        if not tipFound:
            self.fixTip(obj)
        
        if obj.ShownFeature == None and obj.Tip != None:
            obj.ShownFeature = obj.Tip
            obj.ShownFeature.Visibility = True
        
        App.Console.PrintLog(f"Time to recompute: {str(time.time() - startTime)}\n")

        obj.purgeTouched()
    
    def addOrigin(self, obj, origin):
        obj.Origin = origin

        self.addObject(obj, origin)
        
    def execute(self, obj):
        self.recalculateShapes(obj)
    
    def getFullGroup(self, obj):
        group = obj.Group

        for item in obj.Group:
            if hasattr(item, "Group"):
                group.extend(item.Group)
        
        return group
            
    def onChanged(self, obj, prop):
        if prop == "Group":
            if hasattr(self, "oldGroup"):
                newObjects = list(set(obj.Group) - set(self.oldGroup))

                for newItem in newObjects:
                    if isGearsWBPart(newItem) and not isType(newItem, "GearsWBPart"):
                        fixGear(newItem, obj, True)
            
            self.oldGroup = obj.Group

    def dumps(self):
        return None
    
    def loads(self, state):
        return None
    
class ViewProviderPartContainer:
    def __init__(self, vobj = None):
        if vobj is not None:
            vobj.Proxy = self
            self.Object = vobj
    
    def attach(self, vobj):
        self.Object = vobj
        self.updateExtensions(vobj)
    
    def updateExtensions(self, vobj):
        if vobj.Object.hasExtension("App::OriginGroupExtensionPython"):
            vobj.addExtension("Gui::ViewProviderOriginGroupExtensionPython")
    
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
            return False
        else:
            Gui.ActiveDocument.ActiveView.setActiveObject("ConstraintDesign", None)
            return False

    def unsetEdit(self, vobj, mode):
        Gui.ActiveDocument.ActiveView.setActiveObject(vobj.Object.Name, None)
        return True

    def onChanged(self, vobj, prop):
        # Called when a property of the viewobject changes
        return

    def getIcon(self):
        # Return a custom icon (optional)
        return os.path.join(os.path.dirname(__file__), "icons", "ConstraintPart.svg")
    
    # def claimChildren(self):
        # App.Console.PrintMessage('claimChildren called\n')
        # if hasattr(self, "Object"):
            # return self.Object.Object.Group
        # return []

    # def dragObject(self, obj):
        # App.Console.PrintMessage(obj)

    def __getstate__(self):
        # Called when saving
        return None

    def __setstate__(self, state):
        # Called when restoring
        return None

    def dumps(self):
        return None
    
    def loads(self, state):
        return None
    
def makePartContainer():
    obj = App.ActiveDocument.addObject("Part::FeaturePython",
                             "PartContainer")
    PartContainer(obj)
    ViewProviderPartContainer(obj.ViewObject)

    return obj