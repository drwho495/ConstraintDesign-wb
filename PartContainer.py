import FreeCAD as App
import FreeCADGui as Gui
import Part
import time
import os
from Utils import MojoUtils
import json
import Cache.DocumentCacheManager as DocumentCacheManager
from Utils import Utils
from Utils import Constants
from Entities.FeatureCopy import makeFeatureCopy

class PartContainer:
    def updateProps(self, obj, isLink = False):
        if not obj.hasExtension("App::OriginGroupExtensionPython"):
            obj.addExtension("App::OriginGroupExtensionPython")
            
            obj.Origin = App.ActiveDocument.addObject("App::Origin", "Origin")

            if hasattr(obj, "Group"): self.oldGroup = obj.Group

        if (not hasattr(obj, "FastRecompute")
            and ((not hasattr(obj, "IsLink") and isLink == False)
                or (hasattr(obj, "IsLink") and obj.IsLink == False))
        ):
            obj.addProperty("App::PropertyBool", "FastRecompute", "ConstraintDesign", "This property tells the part container whether to only recompute its features if they have been modified by the user.")
            obj.FastRecompute = True

        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "PartContainer"
        
        if not hasattr(obj, "IsLink"):
            obj.addProperty("App::PropertyBool", "IsLink", "ConstraintDesign", "This property tells the part container that it is a link to another part container.")
            obj.IsLink = False
            obj.setEditorMode("IsLink", 3)
        
        if not hasattr(obj, "ObjectLinkFilePath"):
            obj.addProperty("App::PropertyString", "ObjectLinkFilePath", "ConstraintDesign", "This property defines where the object to link is.")
            obj.ObjectLinkFilePath = ""
            obj.setEditorMode("ObjectLinkFilePath", 3)
        
        if not hasattr(obj, "ObjectLinkName"):
            obj.addProperty("App::PropertyString", "ObjectLinkName", "ConstraintDesign", "This property defines where the object to link is.")
            obj.ObjectLinkName = ""
            obj.setEditorMode("ObjectLinkName", 3)
        
        if not hasattr(obj, "LinkFeature"):
            obj.addProperty("App::PropertyXLink", "LinkFeature", "ConstraintDesign", "The link feature of this link.")
            obj.setEditorMode("LinkFeature", 3)
        
        if not hasattr(obj, "ExposedGeometryGroup"):
            obj.addProperty("App::PropertyXLink", "ExposedGeometryGroup", "ConstraintDesign", "The group that contains linked exposed geometry.")
            obj.setEditorMode("ExposedGeometryGroup", 3)
        
        if not hasattr(obj, "JointGroup"):
            obj.addProperty("App::PropertyXLink", "JointGroup", "ConstraintDesign", "The group that contains linked joints.")
            obj.setEditorMode("JointGroup", 3)
        
        if not hasattr(obj, "VariableContainer"):
            obj.addProperty("App::PropertyXLink", "VariableContainer", "ConstraintDesign", "The variable container of this object.")
        
        if not hasattr(obj, "ObjectVisibilityDict"):
            obj.addProperty("App::PropertyString", "ObjectVisibilityDict", "ConstraintDesign", "Type of constraint design feature.")
            obj.setEditorMode("ObjectVisibilityDict", 3)
            obj.ObjectVisibilityDict = "{}"
        
        if (not hasattr(obj, "LinkTipName") 
            and ((not hasattr(obj, "IsLink") and isLink == True)
                or (hasattr(obj, "IsLink") and obj.IsLink == True))
        ):
            obj.addProperty("App::PropertyEnumeration", "LinkTipName", "ConstraintDesign", "The tip to copy from the object that this container links to.")
            obj.LinkTipName = [""]
            obj.LinkTipName = ""

        if not hasattr(obj, "Tip"):
            obj.addProperty("App::PropertyXLink", "Tip", "ConstraintDesign", "The tip feature of the container.")
        
        if not hasattr(obj, "Frozen"):
            obj.addProperty("App::PropertyBool", "Frozen", "ConstraintDesign", "This property stops a PartContainer and its features from recalculating. You should use this when assembling parts. Sketches are still solved.")

        if not hasattr(obj, "Recalculating"):
            obj.addProperty("App::PropertyBool", "Recalculating", "ConstraintDesign")
            obj.setEditorMode("Recalculating", 3)

        if not hasattr(obj, "ShownFeature"):
            obj.addProperty("App::PropertyXLink", "ShownFeature", "ConstraintDesign", "The feature that is being shown.")

    def __init__(self, obj = None, isLink = False):
        if obj is not None:
            obj.Proxy = self

            if hasattr(obj, "Group"): self.oldGroup = obj.Group
            self.updateProps(obj, isLink)
    
    def updateSupportVisibility(self, obj, supportObject, updateDict = True):
        if obj.ObjectVisibilityDict != "{}":
            self.resetVisibility(obj)
        
        objectVisibilityDict = {}

        if not hasattr(obj, "ObjectVisibilityDict"):
            self.updateProps(obj)
        
        if Utils.isType(supportObject, Constants.supportTypes):
            feature = Utils.getParent(supportObject, Constants.featureTypes)
            group = self.getGroup(obj, True, True)

            if feature != None:
                cutoffIndex = group.index(feature)

                if updateDict:
                    for item in obj.Group:
                        objectVisibilityDict[item.Name] = item.Visibility # has to be run seperately, the visibilities change when they shouldn't sometimes

                for item in group:
                    itemGroup = [item]
                    hide = False

                    if item in supportObject.OutList or Utils.isType(supportObject, Constants.datumTypes) or item == feature or group.index(item) > cutoffIndex:
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
    
    def setLinkFeature(self, obj, linkFeature):
        if hasattr(obj, "IsLink") and hasattr(obj, "LinkFeature") and obj.IsLink:
            obj.LinkFeature = linkFeature
    
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
                    deps = Utils.getDependencies(feature, obj)

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

        tipContainer = feature.Proxy.getContainer(feature)

        # make sure this feature is not from a partcontainer nested in this one
        if tipContainer.Name == obj.Name:
            obj.Tip = feature
            feature.Proxy.updateVisibility(feature, True, True)
            self.setShownObj(obj, feature)
            feature.Proxy.updateVisibility(feature, True, True)

    def setShownObj(self, obj, feature):
        inEdit = Gui.ActiveDocument.getInEdit()

        if obj.ShownFeature == feature or (inEdit != None and Utils.isType(inEdit.Object, "BoundarySketch")):
            return
        
        obj.ShownFeature = feature
        group = self.getGroup(obj, False, True)
        setBoundary = True

        for item in group:
            if not hasattr(item, "Proxy") or not hasattr(item.Proxy, "updateVisibility"): 
                item.Visibility = False
                continue
            
            if item.Name != feature.Name:
                item.Proxy.updateVisibility(item, False, setBoundary)
            else:
                setBoundary = False # don't show boundaries that are past the tip

    def getGroup(self, obj, withNonFeatureEntities = False, skipSketch=False):
        filteredGroup = []
        for item in obj.Group:
            if (hasattr(item, "Type") and item.Type in Constants.featureTypes) or (Utils.isType(item, "BoundarySketch") and not skipSketch) or (withNonFeatureEntities and Utils.isType(item, Constants.datumTypes)):
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
            if Utils.isType(item, type) and item.Name not in excludeObjectNames:
                sortedGroup.append(item)
        
        return sortedGroup
    
    def fixTip(self, obj):
        if obj.Tip == None or not obj.Tip in obj.Group:
            group = self.getGroup(obj, False, True)
            
            if len(group) > 0:
                self.setTip(obj, group[-1])

    def recalculateShapes(self, obj, startObj = None, force = False):
        self.updateProps(obj)
        obj.Recalculating = True

        if obj.IsLink:
            if len(obj.ObjectLinkFilePath) != 0 and len(obj.ObjectLinkName) != 0:
                linkObj = Utils.getDocumentByFileName(obj.ObjectLinkFilePath).getObject(obj.ObjectLinkName)

                if linkObj:
                    if obj.LinkFeature == None:
                        newLinkFeature = makeFeatureCopy(2, linkObj, obj)

                        obj.LinkFeature = newLinkFeature
                    
                    if hasattr(linkObj, "VariableContainer") and linkObj.VariableContainer != None:
                        properties = Utils.getVariablesOfVariableContainer(linkObj.VariableContainer)

                        for name, val in properties.items():
                            if not hasattr(obj, name):
                                obj.addProperty(val["Type"], name, "Variables")
                                
                                setattr(obj, name, val["Value"])
            if obj.ExposedGeometryGroup == None:
                obj.ExposedGeometryGroup = obj.Document.addObject("App::DocumentObjectGroup", "ExposedGeometryGroup")
                obj.Proxy.addObject(obj, obj.ExposedGeometryGroup)

            if obj.JointGroup == None:
                obj.JointGroup = obj.Document.addObject("App::DocumentObjectGroup", "JointGroup")
                obj.Proxy.addObject(obj, obj.JointGroup)

        if obj.Frozen and not force:
            obj.purgeTouched()
            return

        prevShape = Part.Shape()
        startTime = time.time()
        inEdit = Gui.ActiveDocument.getInEdit()

        if hasattr(obj, "Group"): self.oldGroup = obj.Group

        if inEdit != None and Utils.isType(inEdit.Object, "BoundarySketch"):
            return
        
        if obj.ObjectVisibilityDict != "{}":
            self.resetVisibility(obj)

        tipFound = False
        foundModifiedFeat = not obj.FastRecompute if hasattr(obj, "FastRecompute") else True # links don't have this prop
        group = self.getGroup(obj, True)
        startIndex = 0

        recomputedNameList = []

        if startObj != None and startObj in group:
            startIndex = group.index(startObj)

        # handle features
        for i, child in enumerate(group):
            if Utils.isType(child, "BoundarySketch"):
                child.Proxy.updateSketch(child, obj)
            elif Utils.isType(child, Constants.featureTypes):
                if (not foundModifiedFeat 
                    and (not hasattr(child, "Modified")
                         or child.Modified
                   )
                ):
                    foundModifiedFeat = True

                if (i >= startIndex
                    and not child.Suppressed
                ):
                    if hasattr(child.Proxy, "getSupports"):
                        supports = child.Proxy.getSupports(child)

                        if len(supports) != 0:
                            depList = []
                            
                            for support in supports:
                                depList.extend(support.OutList)

                            for item in depList:
                                if (Utils.isType(item, Constants.datumTypes) 
                                    and item.Name not in recomputedNameList 
                                    and hasattr(item.Proxy, "generateShape")
                                ):
                                    item.Proxy.generateShape(item, Part.Shape())
                                    recomputedNameList.append(item.Name)

                    if foundModifiedFeat:
                        startTime2 = time.time()
                        newShape = child.Proxy.generateShape(child, prevShape).copy()
                        newShape.ElementMap = {}
                        
                        if hasattr(child, "Modified"):
                            child.Modified = False

                        App.Console.PrintLog(f"Time to recompute {child.Label}: {str(time.time() - startTime2)}\n")
                    elif hasattr(child, "Shape"):
                        newShape = child.Shape

                    recomputedNameList.append(child.Name)

                    if not newShape.isNull():
                        prevShape = newShape
                else:
                    if hasattr(child, "Shape"):
                        child.Shape = prevShape

                if obj.ShownFeature != child:
                    child.Visibility = False # only set to false to avoid recursion

                if obj.Tip != None and child == obj.Tip:
                    tipFound = True

            child.purgeTouched()

        # handle datums that haven't already been recomputed
        for item in self.getGroupOfTypes(obj, Constants.datumTypes, recomputedNameList):
            if hasattr(item.Proxy, "generateShape"):
                item.Proxy.generateShape(item, Part.Shape())
        
        if not tipFound:
            self.fixTip(obj)
        
        if obj.ShownFeature == None and obj.Tip != None:
            obj.ShownFeature = obj.Tip
            obj.ShownFeature.Visibility = True
        
        App.Console.PrintLog(f"Time to recompute: {str(time.time() - startTime)}\n")

        obj.Recalculating = False
        obj.purgeTouched()
    
    def addOrigin(self, obj, origin):
        obj.Origin = origin

        self.addObject(obj, origin)
    
    # if allow cached is enabled, then we will try to find the cached document if this is currently a variant link
    def getLinkedObj(self, obj, allowCached = False):
        self.updateProps(obj)

        if obj.IsLink:
            if len(obj.ObjectLinkFilePath) != 0:
                document = Utils.getDocumentByFileName(obj.ObjectLinkFilePath)

                if document != None and len(obj.ObjectLinkName) != 0:
                    linkedObj = document.getObject(obj.ObjectLinkName)

                    if (allowCached 
                        and obj.LinkFeature != None 
                        and hasattr(obj.LinkFeature, "IsVariantLink") 
                        and obj.LinkFeature.IsVariantLink
                    ):
                        _, cachedObj = DocumentCacheManager.getCacheDocumentAndContainer(linkedObj, obj)

                        if cachedObj != None:
                            return cachedObj
                        else:
                            return linkedObj
                    else:
                        return linkedObj
        return None
    
    def deleteChild(self, obj, child):
        if child in obj.Group:
            fixTip = obj.Tip == None or child.Name == obj.Tip.Name

            document = obj.Document

            if hasattr(child.ViewObject, "Proxy") and child.ViewObject.Proxy != None:
                onDelete = child.ViewObject.Proxy.onDelete(child.ViewObject, [])

                if onDelete == False:
                    return

            document.removeObject(child.Name)

            if fixTip: self.fixTip(obj)
        
    def execute(self, obj):
        self.updateProps(obj)

        if not obj.Frozen:
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
                removedObjects = list(set(self.oldGroup) - set(obj.Group))

                for newItem in newObjects:
                    if Utils.isGearsWBPart(newItem) and not Utils.isType(newItem, "GearsWBPart"):
                        Utils.fixGear(newItem, obj, True)
                    elif newItem.TypeId == "App::VarSet" and obj.VariableContainer == None:
                        obj.VariableContainer = newItem
                
                for removedItem in removedObjects:
                    if removedItem == obj.VariableContainer:
                        obj.VariableContainer = None
            
            self.oldGroup = obj.Group

        if prop == "LinkTipName" and hasattr(obj, "LinkFeature") and obj.LinkFeature != None:
            obj.LinkFeature.UpdateObject = True

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
        if (hasattr(self, "Object") 
            and self.Object != None 
            and self.Object.Object != None
            and hasattr(self.Object.Object, "IsLink")
            and self.Object.Object.IsLink
        ):
            return os.path.join(os.path.dirname(__file__), "icons", "ConstraintLinkPart.svg")
        else:
            return os.path.join(os.path.dirname(__file__), "icons", "ConstraintPart.svg")
    
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
    
def makePartContainer(linkToObject = None):
    name = "PartContainer"
    isLink = False

    if linkToObject != None:
        if linkToObject.Document.FileName == "":
            App.Console.PrintError("Please save the document of the selected object before continuing!\n")
            return None

        isLink = True
        name = "ConstraintLink"

    obj = App.ActiveDocument.addObject("Part::FeaturePython",
                             name)
    PartContainer(obj)
    ViewProviderPartContainer(obj.ViewObject)

    if isLink:
        obj.ExposedGeometryGroup = obj.Document.addObject("App::DocumentObjectGroup", "ExposedGeometryGroup")
        obj.JointGroup = obj.Document.addObject("App::DocumentObjectGroup", "JointGroup")
        obj.Proxy.addObject(obj, obj.ExposedGeometryGroup)
        obj.Proxy.addObject(obj, obj.JointGroup)

        obj.IsLink = True
        obj.Proxy.setLinkFeature(obj, makeFeatureCopy(2, linkToObject, obj))
        
        filePath = linkToObject.Document.FileName
        obj.ObjectLinkFilePath = os.path.relpath(filePath, os.path.dirname(filePath))
        obj.ObjectLinkName = linkToObject.Name
    else:
        # after creating the container, 
        # set it as the active object to make the user's workflow easier
        obj.ViewObject.Proxy.setEdit(obj.ViewObject, None)

    return obj