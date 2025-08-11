import FreeCAD as App
import FreeCADGui as Gui
import Part
import sys
import os
import json
import string
import random
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
import Cache.DocumentCacheManager as DocCacheManager
from Utils.Utils import isType, makeBoundaryCompound, getIDsFromSelection, getPlaneFromStringIDList, getDocumentByFileName, getVariablesOfVariableContainer
from Utils.Constants import *
from Entities.Feature import Feature

# this is a type of feature that copies another part container (Derive, PartMirror, and LinkFeature all originate from this class)
# 0 is PartMirror
# 1 is Derive
# 2 is LinkFeature

class FeatureCopy(Feature):
    def __init__(self, obj, copyType = 0):
        obj.Proxy = self
        self.updateProps(obj, copyType)
        
    def updateProps(self, obj, copyType):
        super(FeatureCopy, self).updateProps(obj, hasRemove = False)

        if not hasattr(obj, "Boundary"):
            obj.addProperty("App::PropertyXLink", "Boundary", "ConstraintDesign")
            obj.setEditorMode("Boundary", 3)
        
        if (hasattr(obj, "CopyType") and obj.CopyType != 2) or (not hasattr(obj, "CopyType") and copyType != 2):
            if not hasattr(obj, "Support"):
                obj.addProperty("App::PropertyXLink", "Support", "ConstraintDesign", "Part container to Mirror")
            
            if not hasattr(obj, "TipName"):
                obj.addProperty("App::PropertyEnumeration", "TipName", "ConstraintDesign", "The Tip of the Part Container to mirror.")
                obj.TipName = [""]
                obj.TipName = ""
            
            if (hasattr(obj, "CopyType") and obj.CopyType == 0) or (not hasattr(obj, "CopyType") and copyType == 0):
                if not hasattr(obj, "PlaneType"):
                    obj.addProperty("App::PropertyString", "PlaneType", "ConstraintDesign", "The type of plane to mirror about.")
                    obj.PlaneType = "None"
                
                if not hasattr(obj, "PlaneHash"):
                    obj.addProperty("App::PropertyStringList", "PlaneHash", "ConstraintDesign", "The plane (as a set of hashes) to mirror about.")
                    obj.PlaneHash = []
                
                if not hasattr(obj, "PlaneFace"):
                    obj.addProperty("App::PropertyXLinkSubList", "PlaneFace", "ConstraintDesign", "The plane (as a face) to mirror about.")
                    obj.PlaneHash = []
        else:
            if not hasattr(obj, "UpdateObject"):
                obj.addProperty("App::PropertyBool", "UpdateObject", "ConstraintDesign", "Marks if this LinkFeature should be updated.")
                obj.UpdateObject = False
        
        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "FeatureCopy"
        
        if not hasattr(obj, "CopyType"):
            obj.addProperty("App::PropertyInteger", "CopyType", "ConstraintDesign", "Type of Feature Copy.")
            obj.CopyType = copyType
        
        if not hasattr(obj, "Group"):
            obj.addProperty("App::PropertyLinkList", "Group", "ConstraintDesign", "Group")
    
    def setBoundary(self, obj, boundary):
        obj.Boundary = boundary

        group = obj.Group
        group.append(boundary)
        obj.Group = group
        
    def setSupport(self, obj, support):
        if hasattr(obj, "Support"):
            obj.Support = support
    
    def getContainer(self, obj):
        return super(FeatureCopy, self).getContainer(obj)

    # Format {"HashName": {"Element:" edge, "GeoId", sketchGeoId, "Occurrence": 0-∞, "FeatureType": Sketch, SketchProj, WiresDatum}}
    def updateElement(self, element, id, map, occurrence = 0, featureType = "Sketch"):
        hasElement = False

        for key, value in map.items():
            if value["GeoId"] == id and value["Occurrence"] == occurrence and value["FeatureType"] == featureType:
                map[key]["Element"] = str(element[0].Name) + "." + str(element[1])

                hasElement = True

        if hasElement == False:
            hash = super(FeatureCopy, self).generateHashName(map)
            
            map[hash] = {"Element": str(element[0].Name) + "." + str(element[1]), "GeoId": id, "Occurrence": occurrence, "FeatureType": featureType}
        
        return map
    
    def generateShape(self, obj, prevShape):
        self.updateProps(obj, obj.CopyType)

        newShape = Part.Shape()
        boundaryShape = Part.Shape()
        supportContainer = None
        container = self.getContainer(obj)
        createVariantLink = False
        cachedObjectChanged = False
        tipName = ""

        if obj.CopyType == 2:
            tipName = container.LinkTipName

            if not hasattr(container, "IsLink") and container.IsLink == False:
                raise Exception("LinkFeature's must be put into ConstraintLink Objects!\n")

            if (container != None 
                and hasattr(container, "ObjectLinkFilePath") 
                and container.ObjectLinkFilePath != None
                and container.ObjectLinkFilePath != ""
                and hasattr(container, "ObjectLinkName")
                and container.ObjectLinkName != None
                and container.ObjectLinkName != ""
            ):
                linkDocument = getDocumentByFileName(container.ObjectLinkFilePath)
                supportContainer = linkDocument.getObject(container.ObjectLinkName)

                if (supportContainer != None 
                    and hasattr(supportContainer, "VariableContainer") 
                    and supportContainer.VariableContainer != None
                ):
                    variables = supportContainer.VariableContainer
                    properties = getVariablesOfVariableContainer(variables)
                    cacheDocument = None
                    cachedContainer = None

                    for name, val in properties.copy().items():
                        containerVal = getattr(container, name)
                        if hasattr(container, name) and containerVal != val["Value"]:
                            createVariantLink = True
                    
                    if createVariantLink:
                        cacheDocument, cachedContainer = DocCacheManager.getCacheDocument(supportContainer, container)

                        if cachedContainer != None and hasattr(cachedContainer, "VariableContainer"):
                            for name, val in properties.copy().items():
                                if not hasattr(cachedContainer.VariableContainer, name):
                                    obj.UpdateObject = True
                                    break

                        if obj.UpdateObject or cachedContainer == None:
                            cachedContainer = DocCacheManager.setPartContainer(cacheDocument, supportContainer)
                        
                        if (cachedContainer != None # just do one more check, just in case
                            and hasattr(supportContainer, "VariableContainer")
                        ):
                            for name, val in properties.copy().items():
                                containerVal = getattr(container, name)
                                if containerVal != getattr(cachedContainer.VariableContainer, name):
                                    cachedObjectChanged = True
                                    setattr(cachedContainer.VariableContainer, name, containerVal)
                    
                        if cachedContainer != None:
                            supportContainer = cachedContainer
                            cacheDocument.recompute()
                        else:
                            createVariantLink = False
        else:
            tipName = obj.TipName

            if obj.Support != None and isType(obj.Support, "PartContainer"):
                supportContainer = obj.Support

        if supportContainer != None:
            pcGroup = supportContainer.Proxy.getGroup(supportContainer, False, True)

            if pcGroup != None or len(pcGroup) != 0:
                nameGroup = []
                updateName = (tipName == "")

                for item in pcGroup:
                    nameGroup.append(item.Name)
                
                if obj.CopyType != 2:
                    obj.TipName = nameGroup
                else:
                    container.LinkTipName = nameGroup

                if updateName:
                    if obj.CopyType != 2:
                        obj.TipName = supportContainer.Tip.Name
                    else:
                        container.LinkTipName = supportContainer.Tip.Name
                
                # we update it like this because we dont know if updateName is set and if the enum value is reset or not
                if obj.CopyType != 2:
                    tipName = obj.TipName
                else:
                    tipName = container.LinkTipName

        if obj.CopyType != 2 or (obj.UpdateObject or (createVariantLink and cachedObjectChanged)):
            if isType(supportContainer, "PartContainer"):
                tip = supportContainer.Document.getObject(tipName)
                if tip != None:
                    face = None
                    planeCenter = None
                    normal = None

                    if obj.CopyType == 0:
                        if obj.PlaneType == "Face":
                            face = obj.PlaneFace
                        elif obj.PlaneType == "Hashes":
                            face = getPlaneFromStringIDList(container, obj.PlaneHash, requestingObjectLabel = obj.Label, asFace = True)

                            if face == None:
                                return prevShape
                    
                        planeCenter = face.Vertexes[0].Point
                        normal = face.normalAt(0, 0)
                            
                    features = supportContainer.Proxy.getGroup(supportContainer, False)
                    filteredFeatures = []

                    for feat in features:
                        filteredFeatures.append(feat)

                        if feat.Name == tipName:
                            break

                    boundaryShape, elementMap = makeBoundaryCompound(filteredFeatures, True, obj.Boundary.Name)
                    if obj.CopyType == 0:
                        boundaryShape = boundaryShape.mirror(planeCenter, normal)
                        newShape = tip.Shape.mirror(planeCenter, normal)
                    else:
                        newShape = tip.Shape
                    
                    obj.ElementMap = json.dumps(elementMap)
                    obj.Boundary.Shape = boundaryShape
                    obj.IndividualShape = newShape.copy()

                    # needs to be here instead of in an else because we need to check the elMap
                    if obj.CopyType == 2:
                        if hasattr(container, "JointGroup") and hasattr(container, "ExposedGeometryGroup"):
                            # "UpdateProps" should have the name of properties that reference hashes that need
                            # to be updated
                            copyTypes = {
                                "Joint": {"Group": container.JointGroup, "UpdateProps": ["Support"]},
                                "ExposedGeometry": {"Group": container.ExposedGeometryGroup, "UpdateProps": ["Support"]}
                            }

                            for item in supportContainer.Group:
                                if hasattr(item, "Type") and item.Type in copyTypes:
                                    fixObj = None
                                    group = copyTypes[item.Type]["Group"]

                                    for subItem in container.Group:
                                        if hasattr(subItem, "LinkObjName") and subItem.LinkObjName == item.Name:
                                            fixObj = subItem
                                            break
                                    
                                    if fixObj == None:
                                        fixObj = container.Document.copyObject(item, False, False)
                                        
                                        container.addObject(fixObj)
                                        group.addObject(fixObj)

                                        fixObj.addProperty("App::PropertyString", "LinkObjName")
                                        fixObj.setEditorMode("LinkObjName", 3)
                                        fixObj.LinkObjName = item.Name

                                    if hasattr(fixObj, "AttachmentSupport"):
                                        fixObj.AttachmentSupport = []
                                    
                                    for propName in item.PropertiesList:
                                        typeId = item.getTypeIdOfProperty(propName)

                                        if propName in copyTypes[item.Type]["UpdateProps"]:
                                            if hasattr(item, propName):
                                                prop = getattr(item, propName)

                                                if typeId == "App::PropertyString":
                                                    if "." in prop:
                                                        propArr = prop.split(".")
                                                        propStringID = propArr[-1]

                                                        if len(propStringID) == hashSize and propStringID in elementMap:
                                                            newFullStringId = f"{obj.Name}.{propStringID}"
                                                            setattr(fixObj, propName, newFullStringId)
                                                elif typeId == "App::PropertyStringList":
                                                    newArr = []

                                                    for singleOldID in prop:
                                                        if "." in singleOldID:
                                                            propArr = singleOldID.split(".")
                                                            propStringID = propArr[-1]

                                                            if len(propStringID) == hashSize and propStringID in elementMap:
                                                                newFullStringId = f"{obj.Name}.{propStringID}"
                                                                newArr.append(newFullStringId)
                                                    
                                                    setattr(fixObj, propName, newArr)
                                        elif (hasattr(item, propName) 
                                              and hasattr(fixObj, propName)
                                              and not typeId.startswith("App::PropertyLink") 
                                              and not typeId.startswith("App::PropertyXLink")
                                              and len(fixObj.getPropertyStatus(propName)) != 0
                                              and fixObj.getPropertyStatus(propName)[0] != "ReadOnly"
                                              and propName != "ExpressionEngine" # this is not set as readonly for some reason
                                              and propName != "Visibility"
                                        ):
                                            setattr(fixObj, propName, getattr(item, propName))
                                        
                                        fixObj.recompute()

            if not prevShape.isNull():
                newShape = Part.makeCompound([prevShape, newShape])

            obj.Shape = newShape

            if obj.CopyType == 2:
                obj.UpdateObject = False
        else:
            newShape = obj.Shape

        obj.Boundary.ViewObject.LineWidth = boundaryLineWidth
        obj.Boundary.ViewObject.PointSize = boundaryPointSize
        obj.Boundary.purgeTouched()

        return newShape

    def execute(self, obj):
        if obj.Group == []:
            obj.Group = [obj.Boundary]

        self.updateProps(obj, obj.CopyType)
            
    def onChanged(self, obj, prop):
        super(FeatureCopy, self).onChanged(obj, prop)

        if prop == "TipName" and hasattr(obj, "CopyType") and hasattr(obj, "UpdateObject") and obj.CopyType == 2:
            obj.UpdateObject = True

    def getBoundaries(self, obj, isShape=False):
        if isShape:
            return [obj.Boundary.Shape]
        else:
            return [obj.Boundary]
            
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None

class ViewProviderFeatureCopy:
    def __init__(self, obj):
        obj.Proxy = self
        obj.Selectable = False
        self.Origin = None
    
    def onDelete(self, vobj, subelements):
        if hasattr(vobj.Object, "Boundary"):
            if vobj.Object.Boundary != None:
                vobj.Object.Document.removeObject(vobj.Object.Boundary.Name)

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
        if hasattr(self, "Object") and self.Object != None and self.Object.Object != None:
            if self.Object.Object.CopyType == 0:
                return os.path.join(os.path.dirname(__file__), "..", "icons", "PartMirror.svg")
            elif self.Object.Object.CopyType == 1:
                return os.path.join(os.path.dirname(__file__), "..", "icons", "Derive.svg")
            elif self.Object.Object.CopyType == 2:
                return os.path.join(os.path.dirname(__file__), "..", "icons", "LinkFeature.svg")
    
    def claimChildren(self):
        # App.Console.PrintMessage('claimChildren called\n')
        if hasattr(self, "Object"):
            return [self.Object.Object.Boundary] 
        return []

    def dragObject(self, obj):
        App.Console.PrintMessage(obj)

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
    
def makeFeatureCopy(copyType = 0, copyObject = None, container = None):
    if container == None:
        container = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")

    if container != None and isType(container, "PartContainer"):
        doc = container.Document
        planeType = "None"
        supportSelection = []

        if copyType == 0:
            fullSelection = Gui.Selection.getCompleteSelection()

            if len(fullSelection) >= 2:
                fullSelection = fullSelection[1:]

                for obj in fullSelection:
                    if obj.HasSubObjects:
                        supportSelection.append((obj.Object, obj.SubElementNames[0]))
            
            if len(supportSelection) == 1 and type(supportSelection[0][1]).__name__ == "Face":
                planeType = "Face"
            elif len(supportSelection) > 1:
                planeType = "Hashes"

        if copyObject == None and copyType != 2:
            selection = Gui.Selection.getSelection()
            if len(selection) != 0:
                copyObject = selection[0]

        if (copyType == 2 or copyObject != None) and isType(copyObject, "PartContainer"):
            doc.openTransaction("CreateFeatureCopy")

            name = "FeatureCopy"

            if copyType == 0:
                name = "PartMirror"
            elif copyType == 1:
                name = "Derive"
            elif copyType == 2:
                name = "LinkFeature"

            obj = App.ActiveDocument.addObject("Part::FeaturePython", name)
            boundary = App.ActiveDocument.addObject("Part::Feature", "Boundary")
            boundary.addProperty("App::PropertyString", "Type")
            boundary.Type = "Boundary"

            FeatureCopy(obj, copyType)
            ViewProviderFeatureCopy(obj.ViewObject)

            if copyType == 0:
                obj.PlaneType = planeType

                if planeType == "Face":
                    obj.PlaneFace = copyObject[0]
                elif planeType == "Hashes":
                    hashes = getIDsFromSelection(fullSelection)

                    if (type(hashes) == list and len(hashes) == 0) or hashes == None:
                        App.Console.PrintError("Unable to find string IDs from selection!")
                    
                    obj.PlaneHash = hashes

            if copyType != 2:
                obj.Proxy.setSupport(obj, copyObject)
                obj.UpdateObject = True

            obj.Proxy.setBoundary(obj, boundary)

            if copyType == 2:
                container.Proxy.setLinkFeature(container, obj)

            container.Proxy.addObject(container, obj, True)
            container.Proxy.setTip(container, obj)

            return obj
        else:
            App.Console.PrintError("Selected object is not a sketch!\n")
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")
        