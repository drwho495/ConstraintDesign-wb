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
from Utils.Utils import isType, makeBoundaryCompound
from Utils.Constants import *
from Entities.Feature import Feature

class Derive(Feature):
    def __init__(self, obj):
        obj.Proxy = self
        self.updateProps(obj)
        
    def updateProps(self, obj):
        super(Derive, self).updateProps(obj)

        if not hasattr(obj, "Boundary"):
            obj.addProperty("App::PropertyXLink", "Boundary", "ConstraintDesign")
            obj.setEditorMode("Boundary", 3)
        
        if not hasattr(obj, "Support"):
            obj.addProperty("App::PropertyXLink", "Support", "ConstraintDesign", "Part container to Mirror")
        
        if not hasattr(obj, "TipName"):
            obj.addProperty("App::PropertyString", "TipName", "ConstraintDesign", "The Tip of the Part Container to mirror.")
            obj.TipName = ""
        
        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "Derive"
        
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
        return super(Derive, self).getContainer(obj)

    # Format {"HashName": {"Element:" edge, "GeoId", sketchGeoId, "Occurrence": 0-∞, "FeatureType": Sketch, SketchProj, WiresDatum}}
    def updateElement(self, element, id, map, occurrence = 0, featureType = "Sketch"):
        hasElement = False

        for key, value in map.items():
            if value["GeoId"] == id and value["Occurrence"] == occurrence and value["FeatureType"] == featureType:
                map[key]["Element"] = str(element[0].Name) + "." + str(element[1])

                hasElement = True

        if hasElement == False:
            hash = super(Derive, self).generateHashName(map)
            
            map[hash] = {"Element": str(element[0].Name) + "." + str(element[1]), "GeoId": id, "Occurrence": occurrence, "FeatureType": featureType}
        
        return map
    
    def generateShape(self, obj, prevShape):
        newShape = Part.Shape()
        datumShape = Part.Shape()

        if isType(obj.Support, "PartContainer"):
            if obj.TipName == "":
                obj.TipName = obj.Support.Tip.Name

            tip = obj.Document.getObject(obj.TipName)

            if tip != None:
                features = obj.Support.Proxy.getGroup(obj.Support, False)

                datumShape, elementMap = makeBoundaryCompound(features, True, obj.Boundary.Name)
                datumShape = datumShape
                newShape = tip.Shape

                obj.ElementMap = json.dumps(elementMap)
                
        obj.Boundary.Shape = datumShape
        obj.IndividualShape = newShape.copy()

        if not prevShape.isNull():
            newShape = Part.Compound([prevShape, newShape])

        obj.Shape = newShape
        obj.Boundary.ViewObject.LineWidth = 2
        obj.Boundary.ViewObject.PointSize = boundaryLineWidth
        obj.ViewObject.LineWidth = boundaryPointSize

        obj.Boundary.purgeTouched()

        return newShape

    def execute(self, obj):
        if obj.Group == []:
            obj.Group = [obj.Boundary]

        self.updateProps(obj)
            
    def onChanged(self, obj, prop):
        if prop == "Length":
            obj.touch()

        super(Derive, self).onChanged(obj, prop)


    def getBoundaries(self, obj, isShape=False):
        if isShape:
            return [obj.Boundary.Shape]
        else:
            return [obj.Boundary]
            
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

class ViewProviderDerive:
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
    
def makeDerive():
    activeObject = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")

    if activeObject != None and hasattr(activeObject, "Type") and activeObject.Type == "PartContainer":
        selectedObject = Gui.Selection.getSelection()
        doc = activeObject.Document
        doc.openTransaction("CreateDerive")
        supportSelection = []

        if len(selectedObject) == 0:
            selectedObject = None
        else:
            selectedObject = selectedObject[0]

        if selectedObject != None and isType(selectedObject, "PartContainer"):
            mirror = App.ActiveDocument.addObject("Part::FeaturePython", "Derive")
            boundary = App.ActiveDocument.addObject("Part::Feature", "Boundary")
            boundary.addProperty("App::PropertyString", "Type")
            boundary.Type = "Boundary"

            Derive(mirror)
            ViewProviderDerive(mirror.ViewObject)

            mirror.Proxy.setSupport(mirror, selectedObject)
            mirror.Proxy.setBoundary(mirror, boundary)

            activeObject.Proxy.addObject(activeObject, mirror, True)
            activeObject.Proxy.setTip(activeObject, mirror)
        else:
            App.Console.PrintError("Selected object is not a sketch!\n")
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")