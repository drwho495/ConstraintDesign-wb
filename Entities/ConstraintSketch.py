import FreeCAD as App
import FreeCADGui as Gui
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from Utils import Utils
from Utils import SketchUtils
from Utils import Constants
from Entities.ExposedGeo import makeExposedGeo
from Entities.Entity import Entity
from PySide import QtWidgets
import Part
from Utils import GuiUtils

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

        if document != None and objectName != None:
            object = document.getObject(objectName)

            if object != None and object != self.sketch:
                container = Utils.getParent(self.sketch, "PartContainer")

                if Utils.isType(object, "ExposedGeometry") and hasattr(object, "UseCase") and object.UseCase == "Sketch":
                    return

                if container != None:
                    stringId = Utils.getStringID(container, (object, elementName))

                    if stringId != None:
                        Gui.Selection.clearSelection()

                        if hasattr(self.sketch, "Proxy") and hasattr(self.sketch.Proxy, "addStringIDExternalGeo"):
                            self.sketch.Proxy.addStringIDExternalGeo(self.sketch, stringId, container = container)
                        else:
                            App.Console.PrintError("Constraint design did not setup this sketch properly!\nPlease report!\n")
                        
class ConstraintSketchTaskPanel:
    def __init__(self, obj):
        self.form = QtWidgets.QWidget()
        self.form.destroyed.connect(self.close)
        self.sketch = obj

        layout = QtWidgets.QVBoxLayout(self.form)
        layout.addWidget(QtWidgets.QLabel(f"Editing: {obj.Label}"))

        buttonLayout = QtWidgets.QHBoxLayout()
        self.applyButton = QtWidgets.QPushButton("Apply")
        self.updateButton = QtWidgets.QPushButton("Update")
        self.cancelButton = QtWidgets.QPushButton("Cancel")

        buttonLayout.addWidget(self.applyButton)
        buttonLayout.addWidget(self.updateButton)
        buttonLayout.addWidget(self.cancelButton)
        layout.addLayout(buttonLayout)

        self.oldSupportHashes = list(getattr(obj, 'SupportHashes', []))
        self.container = Utils.getParent(obj, "PartContainer")
        self.selector = GuiUtils.SelectorWidget(sizeLimit=4, addOldSelection=True, startSelection=self.oldSupportHashes, container=self.container)
        self.selector.selectionChanged.connect(self.selectionChanged)
        layout.addWidget(self.selector)

        self.applyButton.clicked.connect(self.accept)
        self.updateButton.clicked.connect(self.update)
        self.cancelButton.clicked.connect(self.reject)

    def selectionChanged(self, newSelection=[]):
        pass

    def close(self):
        self.selector.cleanup()
        Gui.Control.closeDialog()

    def update(self):
        sel = self.selector.getSelection()
        self.sketch.SupportHashes = sel
        self.sketch.Proxy.updateSketch(self.sketch)
        # could call recompute or other update logic here if needed

    def accept(self):
        self.update()
        self.close()

    def reject(self):
        self.sketch.SupportHashes = self.oldSupportHashes
        self.close()

    def getStandardButtons(self):
        return 0

class ConstraintSketch(Entity):
    def __init__(self, obj):
        self.lastProp = ""
        obj.Proxy = self
        self.updateProps(obj)
    
    def attach(self, obj):
        self.lastProp = ""
        self.updateProps(obj)
    
    def onChanged(self, obj, prop): # needed for versions of the program where the sketch python isnt bugged
        if not hasattr(self, "lastProp"):
            self.lastProp = ""

        if prop == "Constraints" and self.lastProp != prop: # dont ask
            if not SketchUtils.hasExternalGeometryBug():
                for i, exGeo in enumerate(obj.ExternalGeometry):
                    object = exGeo[0]

                    if not Utils.isType(object, Constants.datumTypes):
                        obj.delExternal(i)
        
        self.lastProp = prop

    def addStringIDExternalGeo(self, obj, stringID, container = None):
        if container == None:
            container = Utils.getParent(obj, "PartContainer")
        
        exposedGeo = makeExposedGeo(stringID, container, "Sketch")
        exposedGeo.Proxy.generateShape(exposedGeo, Part.Shape())
        exposedGeo.ViewObject.ShowInTree = False
        exposedGeo.Visibility = False
        elementName = ""

        if hasattr(exposedGeo, "IsSetup"):
            exposedGeo.IsSetup = True

        if len(exposedGeo.Shape.Edges) == 0:
            if len(exposedGeo.Shape.Vertexes) != 0:
                elementName = "Vertex1"
        else:
            elementName = "Edge1"
        
        if int(App.Version()[0]) >= 1 and int(App.Version()[1]) >= 1:
            obj.addExternal(exposedGeo.Name, elementName, True, False)
        else:
            obj.addExternal(exposedGeo.Name, elementName)

        obj.recompute()
    
    def updateSketch(self, obj, container=None):
        if container == None:
            container = Utils.getParent(obj, "PartContainer")

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
            if obj.SupportType == "Hashes" and len(obj.SupportHashes) != 0:
                plane = SketchUtils.getPlaneFromStringIDList(container, obj.SupportHashes, obj.Label)

                if plane != None:
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

    def showGui(self, obj):
        Gui.Control.showDialog(ConstraintSketchTaskPanel(obj))

class ConstraintSketchViewObject:
    def __init__(self, vobj):
        vobj.Object.recompute()
        vobj.Proxy = self
        self.observer = None
    
    # def onDelete(self, vobj, _):
    #     try:
    #         for item in vobj.Object.OutList:
    #             if Utils.isType(item, "ExposedGeometry") and hasattr(item, "UseCase") and item.UseCase == "Sketch":
    #                 item.Document.removeObject(item.Name)
    #     except Exception as e:
    #         App.Console.PrintWarning(f"{str(e)} occured while trying to delete sketch dependencies!\n")
        
    #     return True
    
    def setEdit(self, vobj, _):
        App.Console.PrintLog(f"{vobj.Object.Label} was opened.\n")
        
        if not hasattr(self, "observer"): self.observer = None # trying to avoid using attach

        if self.observer != None:
            self.observer.cleanup()

        self.observer = ExternalGeoSelector(vobj.Object)
        container = vobj.Object.Proxy.getContainer(vobj.Object)

        if container != None:
            container.Proxy.updateSupportVisibility(container, vobj.Object)
        vobj.Object.Document.openTransaction("OpenConstraintSketch")
        
        # App.setActiveTransaction("EditSketch")

    def unsetEdit(self, vobj, _):
        App.Console.PrintLog(f"{vobj.Object.Label} was closed.\n")

        if not hasattr(self, "observer"): self.observer = None # trying to avoid using attach

        if self.observer != None:
            self.observer.cleanup()
            
        container = vobj.Object.Proxy.getContainer(vobj.Object)

        if container != None:
            container.Proxy.resetVisibility(container)
        vobj.Object.Document.openTransaction("CloseConstraintSketch")
    
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

    if activeObject != None and Utils.isType(activeObject, "PartContainer"):
        activeObject.Proxy.addObject(activeObject, obj)
    
    if editAfter:
        obj.recompute()
        Gui.ActiveDocument.setEdit(obj)

    # obj.recompute()
    # obj.ViewObject.Proxy = 0