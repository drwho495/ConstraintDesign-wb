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
from Utils import Utils
from Utils import Constants
from Entities.Feature import Feature

# this needs to be merged with Derive in a class like PartShapeCopy

class PartMirror(Feature):
    def __init__(self, obj):
        obj.Proxy = self
        self.updateProps(obj)
        
    def updateProps(self, obj):
        super(PartMirror, self).updateProps(obj)

        if not hasattr(obj, "Boundary"):
            obj.addProperty("App::PropertyXLink", "Boundary", "ConstraintDesign")
            obj.setEditorMode("Boundary", 3)
        
        if not hasattr(obj, "Support"):
            obj.addProperty("App::PropertyXLink", "Support", "ConstraintDesign", "Part container to Mirror")
        
        if hasattr(obj, "TipName") and obj.getTypeIdOfProperty("TipName") == "App::PropertyString":
            obj.removeProperty("TipName")

        if not hasattr(obj, "TipName"):
            obj.addProperty("App::PropertyEnumeration", "TipName", "ConstraintDesign", "The Tip of the Part Container to mirror.")
            obj.TipName = [""]
            obj.TipName = ""

        if not hasattr(obj, "BoundaryUpToTip"):
            obj.addProperty("App::PropertyBool", "BoundaryUpToTip", "ConstraintDesign", "This tells the boundary generator to ignore features past the tip.")
            obj.BoundaryUpToTip = True
        
        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "PartMirror"
        
        if not hasattr(obj, "PlaneType"):
            obj.addProperty("App::PropertyString", "PlaneType", "ConstraintDesign", "The type of plane to mirror about.")
            obj.PlaneType = "None"
        
        if not hasattr(obj, "PlaneHash"):
            obj.addProperty("App::PropertyStringList", "PlaneHash", "ConstraintDesign", "The plane (as a set of hashes) to mirror about.")
            obj.PlaneHash = []
        
        if not hasattr(obj, "PlaneFace"):
            obj.addProperty("App::PropertyXLinkSubList", "PlaneFace", "ConstraintDesign", "The plane (as a face) to mirror about.")
            obj.PlaneHash = []

        if not hasattr(obj, "Group"):
            obj.addProperty("App::PropertyLinkList", "Group", "ConstraintDesign", "Group")
    
    def setBoundary(self, obj, boundary):
        obj.Boundary = boundary

        group = obj.Group
        group.append(boundary)
        obj.Group = group
        
    def setSupport(self, obj, support):
        obj.Support = support
    
    def getContainer(self, obj):
        return super(PartMirror, self).getContainer(obj)

    # Format {"HashName": {"Element:" edge, "GeoId", sketchGeoId, "Occurrence": 0-∞, "FeatureType": Sketch, SketchProj, WiresDatum}}
    def updateElement(self, element, id, map, occurrence = 0, featureType = "Sketch"):
        hasElement = False

        for key, value in map.items():
            if value["GeoId"] == id and value["Occurrence"] == occurrence and value["FeatureType"] == featureType:
                map[key]["Element"] = str(element[0].Name) + "." + str(element[1])

                hasElement = True

        if hasElement == False:
            hash = super(PartMirror, self).Utils.generateHashName(map)
            
            map[hash] = {"Element": str(element[0].Name) + "." + str(element[1]), "GeoId": id, "Occurrence": occurrence, "FeatureType": featureType}
        
        return map
    
    def generateShape(self, obj, prevShape):
        newShape = Part.Shape()
        datumShape = Part.Shape()

        if Utils.isType(obj.Support, "PartContainer"):
            if obj.Support != None:
                pcGroup = obj.Support.Proxy.getGroup(obj.Support, False, True)

                if pcGroup != None or len(pcGroup) != 0:
                    nameGroup = []
                    updateName = (obj.TipName == "")

                    for item in pcGroup:
                        nameGroup.append(item.Name)
                    
                    obj.TipName = nameGroup

                    if updateName:
                        obj.TipName = obj.Support.Tip.Name

            tip = obj.Document.getObject(obj.TipName)

            if tip != None:
                face = None

                if obj.PlaneType == "Face":
                    face = obj.PlaneFace
                elif obj.PlaneType == "Hashes":
                    container = self.getContainer(obj)

                    face = getPlaneFromStringIDList(container, obj.PlaneHash, requestingObjectLabel = obj.Label, asFace = True)

                    if face == None:
                        return prevShape
                
                planeCenter = face.Vertexes[0].Point
                normal = face.normalAt(0, 0)

                features = obj.Support.Proxy.getGroup(obj.Support, False)
                filteredFeatures = features

                if obj.BoundaryUpToTip:
                    filteredFeatures = []

                    if len(obj.TipName) != 0:
                        for item in features:
                            filteredFeatures.append(item)
                            
                            if item.Name == obj.TipName:
                                break
                            

                datumShape, elementMap = makeBoundaryCompound(filteredFeatures, True, obj.Boundary.Name)
                datumShape = datumShape.mirror(planeCenter, normal)
                newShape = tip.Shape.mirror(planeCenter, normal)

                obj.ElementMap = json.dumps(elementMap)
                
        obj.Boundary.Shape = datumShape
        obj.Boundary.ViewObject.LineWidth = Constants.boundaryLineWidth
        obj.Boundary.ViewObject.PointSize = Constants.boundaryPointSize
        obj.ViewObject.LineWidth = 1
        obj.Boundary.purgeTouched()
        obj.IndividualShape = newShape.copy()

        if not prevShape.isNull():
            newShape = Part.Compound([prevShape, newShape])
        
        obj.Shape = newShape

        return newShape

    def execute(self, obj):
        if obj.Group == []:
            obj.Group = [obj.Boundary]

        self.updateProps(obj)
            
    def onChanged(self, obj, prop):
        super(PartMirror, self).onChanged(obj, prop)


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

class ViewProviderPartMirror:
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
        return os.path.join(os.path.dirname(__file__), "..", "icons", "PartMirror.svg")
    
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
    
def makePartMirror():
    activeObject = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")

    if hasattr(activeObject, "Type") and activeObject != None and activeObject.Type == "PartContainer":
        doc = activeObject.Document
        selectedObject = Gui.Selection.getSelection()
        fullSelection = Gui.Selection.getCompleteSelection()
        planeType = "None"
        supportSelection = []

        if len(fullSelection) >= 2:
            fullSelection = fullSelection[1:]

            for obj in fullSelection:
                if obj.HasSubObjects:
                    supportSelection.append((obj.Object, obj.SubElementNames[0]))
        
        if len(supportSelection) == 1 and type(supportSelection[0][1]).__name__ == "Face":
            planeType = "Face"
        elif len(supportSelection) > 1:
            planeType = "Hashes"

        if len(selectedObject) == 0:
            selectedObject = None
        else:
            selectedObject = selectedObject[0]

        if selectedObject != None and hasattr(selectedObject, "Type") and selectedObject.Type == "PartContainer":
            doc.openTransaction("CreatePartMirror")

            mirror = App.ActiveDocument.addObject("Part::FeaturePython", "PartMirror")
            boundary = App.ActiveDocument.addObject("Part::Feature", "Boundary")
            boundary.addProperty("App::PropertyString", "Type")
            boundary.Type = "Boundary"

            PartMirror(mirror)
            ViewProviderPartMirror(mirror.ViewObject)

            mirror.PlaneType = planeType

            if planeType == "Face":
                mirror.PlaneFace = selectedObject[0]
            elif planeType == "Hashes":
                hashes = Utils.getIDsFromSelection(fullSelection)

                if (type(hashes) == list and len(hashes) == 0) or hashes == None:
                    App.Console.PrintError("Unable to find string IDs from selection!")
                
                mirror.PlaneHash = hashes
                                        
            mirror.Proxy.setSupport(mirror, selectedObject)
            mirror.Proxy.setBoundary(mirror, boundary)

            activeObject.Proxy.addObject(activeObject, mirror, True)
            activeObject.Proxy.setTip(activeObject, mirror)
        else:
            App.Console.PrintError("Selected object is not a sketch!\n")
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")
        