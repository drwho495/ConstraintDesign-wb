import FreeCAD as App
import FreeCADGui as Gui
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from Utils.Utils import isType, getElementFromHash, getParent, getStringID
from Utils.Constants import *
from Entities.ExposedGeo import makeExposedGeo
from Entities.Entity import Entity
from PySide import QtWidgets
import Part
from Utils.GuiUtils import SelectorWidget

class ExternalGeoSelector:
    def __init__(self, sketch):
        Gui.Selection.addObserver(self)
        self.sketch = sketch

    def cleanup(self):
        Gui.Selection.removeObserver(self)

    def addSelection(self, documentName, objectName, elementName, null1 = None, null2 = None): # extra args because of link stage 3
        document = App.getDocument(documentName)
        edit = Gui.ActiveDocument.getInEdit()

        if edit == None or edit.Object != self.sketch:
            self.cleanup()
            return

        try:
            if document != None and objectName != None:
                object = document.getObject(objectName)

                if object != None and object != self.sketch:
                    container = getParent(self.sketch, "PartContainer")

                    if container != None:
                        stringId = getStringID(container, (object, elementName))

                        if stringId != None:
                            if hasattr(self.sketch, "Proxy") and hasattr(self.sketch.Proxy, "addStringIDExternalGeo"):
                                self.sketch.Proxy.addStringIDExternalGeo(self.sketch, stringId, container)
                            else:
                                App.Console.PrintError("Constraint design did not setup this sketch properly!\nPlease report!\n")
                            
                            Gui.Selection.clearSelection()
        except Exception as e:
            App.Console.PrintWarning(f"{self.sketch.Label} errored with: {str(e)}\n")

class ConstraintSketch(Entity):
    def __init__(self, obj):
        obj.Proxy = self
        self.updateProps(obj)
    
    def attach(self, obj):
        self.updateProps(obj)
    
    def onChanged(self, obj, prop):
        pass

    def addStringIDExternalGeo(self, obj, stringID, container = None):
        if container == None:
            container = getParent(obj, "PartContainer")
        
        exposedGeo = makeExposedGeo(stringID, container, "Sketch")
        exposedGeo.Proxy.generateShape(exposedGeo, Part.Shape())
        exposedGeo.ViewObject.ShowInTree = False
        exposedGeo.Visibility = False
        elementName = ""

        if len(exposedGeo.Shape.Edges) == 0:
            if len(exposedGeo.Shape.Vertexes) != 0:
                elementName = "Vertex1"
        else:
            elementName = "Edge1"
        
        obj.addExternal(exposedGeo.Name, elementName, True, False)
        obj.recompute()

    def updateSketch(self, obj, container=None):
        if container == None:
            container = getParent(obj, "PartContainer")

        if hasattr(obj, "Support") and not hasattr(obj, "SupportHashes"):
            obj.addProperty("App::PropertyStringList", "SupportHashes", "Base")
            obj.SupportHashes = obj.Support

            obj.removeProperty("Support")

        if not hasattr(obj, "SupportPlane"): 
            obj.addProperty("App::PropertyXLink", "SupportPlane", "Base")
        
        if not hasattr(obj, "SupportType"): 
            obj.addProperty("App::PropertyEnumeration", "SupportType", "Base")
            obj.SupportType = ["Plane", "Hashes"]
            obj.SupportType = "Hashes"
        
        if hasattr(obj, "SupportType") and hasattr(obj, "SupportPlane") and hasattr(obj, "SupportHashes"):
            if obj.SupportType == "Hashes":
                vectors = []

                for hash in obj.SupportHashes:
                    boundary, elementName = getElementFromHash(container, hash, requestingObjectLabel=obj.Label)

                    if boundary == None or elementName == None: continue

                    element = boundary.Shape.getElement(elementName)

                    if type(element).__name__ == "Edge":
                        if len(element.Vertexes) == 2:
                            vectors.append(element.Vertexes[0].Point)
                            vectors.append(element.Vertexes[1].Point)
                        else:
                            for vertex in element.Vertexes:
                                vectors.append(vertex.Point)
                    elif type(element).__name__ == "Vertex":
                        vectors.append(element.Point)

                if len(vectors) >= 3:
                    p1 = vectors[0]
                    p2 = vectors[1]
                    p3 = vectors[2]

                    plane = Part.Plane(p1, p2, p3)
                    originVector = App.Vector(0,0,0)

                    if hasattr(container.Origin, "Placement"):
                        originVector = container.Origin.Placement.Base
                    
                    position = plane.projectPoint(originVector)

                    obj.Placement = App.Placement(position, plane.Rotation)
            elif obj.SupportType == "Plane":
                obj.SupportPlane.recompute()

                obj.Placement = obj.SupportPlane.Placement
                obj.SupportPlane.purgeTouched() # sometimes it doesn't listen
        obj.recompute()
    
    def updateProps(self, obj):
        if hasattr(obj, "AttacherEngine"):
            obj.setEditorMode("AttacherEngine", 3)
        
        if hasattr(obj, "AttachmentSupport"):
            obj.setEditorMode("AttachmentSupport", 3)
        
        if hasattr(obj, "MapMode"):
            obj.setEditorMode("MapMode", 3)

        if not hasattr(obj, "SupportHashes"):
            obj.addProperty("App::PropertyStringList", "SupportHashes", "Base")
        
        if not hasattr(obj, "SupportPlane"):
            obj.addProperty("App::PropertyXLink", "SupportPlane", "Base")
        
        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "Base")
            obj.Type = "BoundarySketch"

        if not hasattr(obj, "SupportType"):
            obj.addProperty("App::PropertyEnumeration", "SupportType", "Base")
            obj.SupportType = ["Plane", "Hashes"]
            obj.SupportType = "Hashes"

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None

class ConstraintSketchViewObject:
    def __init__(self, vobj):
        vobj.Object.recompute()
        vobj.Proxy = self
        self.observer = None
    
    # def onDelete(self, vobj, _):
    #     try:
    #         for item in vobj.Object.OutList:
    #             if isType(item, "ExposedGeometry") and hasattr(item, "UseCase") and item.UseCase == "Sketch":
    #                 item.Document.removeObject(item.Name)
    #     except Exception as e:
    #         App.Console.PrintWarning(f"{str(e)} occured while trying to delete sketch dependencies!\n")
        
    #     return True
    
    def setEdit(self, vobj, _):
        App.Console.PrintLog(f"{vobj.Object.Label} was opened.\n")
        App.closeActiveTransaction()
        
        if not hasattr(self, "observer"): self.observer = None # trying to avoid using attach

        if self.observer != None:
            self.observer.cleanup()

        self.observer = ExternalGeoSelector(vobj.Object)
        container = vobj.Object.Proxy.getContainer(vobj.Object)

        if container != None:
            container.Proxy.updateSupportVisibility(container, vobj.Object)
        
        # App.setActiveTransaction("EditSketch")

    def unsetEdit(self, vobj, _):
        App.Console.PrintLog(f"{vobj.Object.Label} was closed.\n")
        App.closeActiveTransaction()

        if not hasattr(self, "observer"): self.observer = None # trying to avoid using attach

        if self.observer != None:
            self.observer.cleanup()
        
        container = vobj.Object.Proxy.getContainer(vobj.Object)

        if container != None:
            container.Proxy.resetVisibility(container)
    
    def getIcon(self):
        return os.path.join(os.path.dirname(__file__), "..", "icons", "Sketch.svg")
    
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None

def makeSketch(stringIDs, editAfter=False):
    obj = App.ActiveDocument.addObject("Sketcher::SketchObjectPython", "ConstraintSketch")
    activeObject = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")
    ConstraintSketch(obj)
    ConstraintSketchViewObject(obj.ViewObject)

    if len(stringIDs) != 0:
        obj.SupportHashes = stringIDs

    if activeObject != None and isType(activeObject, "PartContainer"):
        activeObject.Proxy.addObject(activeObject, obj)
    
    if editAfter:
        Gui.ActiveDocument.setEdit(obj)

    # obj.recompute()
    # obj.ViewObject.Proxy = 0