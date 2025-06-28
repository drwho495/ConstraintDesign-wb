import FreeCAD as App
import FreeCADGui as Gui
import Part
import time
import os
from Utils import featureTypes, isType, datumTypes, getDependencies
from Commands.SketchUtils import positionSketch
import json

class PartContainer:
    def updateProps(self, obj):
        if not obj.hasExtension("App::OriginGroupExtensionPython"):
            obj.addExtension("App::OriginGroupExtensionPython")
            
            obj.Origin = App.ActiveDocument.addObject("App::Origin", "Origin")
            # self.addObject(obj, obj.Origin, False)

        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "PartContainer"
        
        if not hasattr(obj, "Tip"):
            obj.addProperty("App::PropertyXLink", "Tip", "ConstraintDesign", "The tip feature of the container.")

        if not hasattr(obj, "ShownFeature"):
            obj.addProperty("App::PropertyXLink", "ShownFeature", "ConstraintDesign", "The feature that is being shown.")

    def __init__(self, obj = None):
        if obj is not None:
            obj.Proxy = self

            self.updateProps(obj)
    
    def attach(self, obj):
        self.updateProps(obj)
    
    def addObject(self, obj, objToAdd, afterTip=False, customAfterFeature = None):
        group = obj.Group

        print("custom feature in group: " + str(customAfterFeature in group))

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
            print("use custom feature")

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
        obj.ShownFeature = feature
        group = self.getGroup(obj, False)
        group.remove(feature)

        for item in group: item.Visibility = False

    def getGroup(self, obj, withNonFeatureEntities = False, skipSketch=False):
        filteredGroup = []
        for item in obj.Group:
            if (hasattr(item, "Type") and item.Type in featureTypes) or (hasattr(item, "TypeId") and item.TypeId == "Sketcher::SketchObject" and not skipSketch) or (withNonFeatureEntities and isType(item, "ExposedGeometry")):
                filteredGroup.append(item)
        
        return filteredGroup
    
    def fixTip(self, obj):
        if not obj.Tip in obj.Group:
            group = self.getGroup(obj, False, True)
            
            if len(group) > 0:
                obj.Tip = group[len(group) - 1]
            #obj.Tip.Visibility = True

    # # Format {"HashName": {"Element:" edge, "GeoId", sketchGeoId, "Occurrence": 0-∞, "FeatureType": Sketch, SketchProj, WiresDatum}}
    # def getBoundariesCompound(self, obj, generateElementMap = False, elementMapFeatureName = ""):
    #     boundaryArray = []
    #     elementMap = {}
    #     newEdgeNum = 0
    #     newVertexNum = 0
    #     edgeIndex = 0
    #     vertexIndex = 0
    #     group = self.getGroup(obj, False)

    #     for item in group:
    #         if not (hasattr(item, "TypeId") and item.TypeId == "Sketcher::SketchObject"):
    #             boundaries = []

    #             if generateElementMap:
    #                 boundaries = item.Proxy.getBoundaries(item, False)
    #             else:
    #                 boundaries = item.Proxy.getBoundaries(item, True)

    #             if generateElementMap and elementMapFeatureName != "" and hasattr(item, "ElementMap"):
    #                 itemElementMap = json.loads(item.ElementMap)
                    
    #                 for boundary in boundaries:
    #                     boundaryArray.append(boundary.Shape)
                    
    #                     for hash, value in itemElementMap.items():
    #                         elementArray = value["Element"].split(".")
    #                         featureName = elementArray[0]
    #                         elementName = elementArray[1]

    #                         if featureName == boundary.Name:
    #                             if elementName.startswith("Edge"):
    #                                 elementNum = int(elementName[4:])
    #                                 elementNum += edgeIndex
    #                                 elementName = "Edge" + str(elementNum)
    #                             elif elementName.startswith("Vertex"):
    #                                 elementNum = int(elementName[6:])
    #                                 elementNum += vertexIndex
    #                                 elementName = "Vertex" + str(elementNum)

    #                             value["Element"] = elementMapFeatureName + "." + elementName
    #                             elementMap[hash] = value
                        
    #                     edgeIndex += len(boundary.Shape.Edges) + 0
    #                     vertexIndex += len(boundary.Shape.Vertexes) + 0
    #             # print(elementMap)        
    #         else: 
    #             print(item.Label)
    #             # boundaryArray.extend(boundaries)
            
    #         print("edge index: " + str(edgeIndex))
    #         print("vertex index: " + str(vertexIndex))

    #         edgeIndex += newEdgeNum
    #         vertexIndex += newVertexNum

        
    #     print("array: " + str(boundaryArray))
        
    #     if generateElementMap:
    #         return Part.Compound(boundaryArray), elementMap
    #     else:
    #         return Part.Compound(boundaryArray)
    
    def recalculateShapes(self, obj, startObj = None):
        prevShape = Part.Shape()
        startTime = time.time()

        if not hasattr(obj, "Tip"):
            self.updateProps(obj)

        tipFound = False
        group = self.getGroup(obj, True)
        startIndex = 0

        if startObj != None and startObj in group:
            startIndex = group.index(startObj)

        for i, child in enumerate(group):
            if hasattr(child, "TypeId") and child.TypeId == "Sketcher::SketchObject":
                
                positionSketch(child, obj)
            elif isType(child, featureTypes):
                print(child.Label)
                print(child.Type)

                if i >= startIndex and not child.Suppressed:
                    newShape = child.Proxy.generateShape(child, prevShape)

                    if not newShape.isNull():
                        prevShape = newShape
                else:
                    if hasattr(child, "Shape"):
                        child.Shape = prevShape

                if obj.ShownFeature != child:
                    child.Visibility = False # only set to false to avoid recursion

                if child == obj.Tip:
                    tipFound = True
            elif hasattr(child, "Type") and child.Type in datumTypes:
                child.Proxy.generateShape(child, prevShape)

            child.purgeTouched()
        
        if not tipFound:
            self.fixTip(obj)
        
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
        pass
    
    """ Element format: featureName.hash """
    # def getElement(self, obj, element):
    #     elementArray = element.split(".")

    #     if len(elementArray) != 2:
    #         App.Console.PrintError("Malformed element reference!\nPlease remove any periods in your feature names\n(If one somehow does contain a period, then you will need to recreate it)\n")
    #     else:
    #         featureName = elementArray[0]
    #         hash = elementArray[1]
    #         featureGroup = self.getFullGroup(obj)
    #         featureInGroup = None

    #         for feature in featureGroup:
    #             if feature.Name == featureName:
    #                 featureInGroup = feature
            
    #         if featureInGroup == None:
    #             App.Console.PrintError("Feature in element reference not found!\n")
    #         else:
    #             try:
    #                 return featureInGroup.Proxy.getElement(featureInGroup, hash)
    #             except Exception as e:
    #                 raise e

    # This is for debugging
    def highlightElement(self, obj, element):
        feature, element = self.getElement(obj, element)

        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(feature, [element])

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
        else:
            print("No extension!")
    
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
    
def makePartContainer():
    obj = App.ActiveDocument.addObject("Part::FeaturePython",
                             "PartContainer")
    PartContainer(obj)
    ViewProviderPartContainer(obj.ViewObject)

    return obj