import FreeCAD as App
import FreeCADGui as Gui
import Part
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from Utils.Utils import isType, getParent, getIDsFromSelection, getObjectsFromScope, getElementFromHash
from Utils.Constants import *
from Entities.Entity import Entity
from PySide import QtWidgets
from Utils.GuiUtils import SelectorWidget

missingStr = "(MISSING) "
useCases = ["Generic", "Sketch"]

class ExposedGeoTaskPanel:
    def __init__(self, obj, addOldSelection=True, startSelection=[]):
        self.form = QtWidgets.QWidget()
        self.form.destroyed.connect(self.close)
        self.exposedGeo = obj

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

        # Now add the selector and labels after the buttons
        self.oldSupport = getattr(obj, 'Support', None)
        self.container = obj.Proxy.getContainer(obj)
        self.selector = SelectorWidget(sizeLimit=1, addOldSelection=addOldSelection, startSelection=[self.oldSupport] if self.oldSupport else [], container=self.container)
        self.selector.selectionChanged.connect(self.selectionChanged)
        layout.addWidget(self.selector)

        if hasattr(obj, 'Missing'):
            self.missingLabel = QtWidgets.QLabel(f"Missing: {obj.Missing}")
            layout.addWidget(self.missingLabel)
        else:
            self.missingLabel = None

        self.applyButton.clicked.connect(self.accept)
        self.updateButton.clicked.connect(self.update)
        self.cancelButton.clicked.connect(self.reject)

    def selectionChanged(self, newSelection=[]):
        # No supportLabel to update
        pass

    def close(self):
        self.selector.cleanup()
        Gui.Control.closeDialog()

    def update(self):
        sel = self.selector.getSelection()
        if sel:
            self.exposedGeo.Support = sel[0]
        self.exposedGeo.Proxy.generateShape(self.exposedGeo, Part.Shape())

    def accept(self):
        self.update()
        self.close()

    def reject(self):
        self.exposedGeo.Support = self.oldSupport
        self.close()

    def getStandardButtons(self):
        return 0

class ExposedGeo(Entity):
    def __init__(self, obj, useCase="Generic"):
        obj.Proxy = self
        self.updateProps(obj, useCase)
    
    def attach(self, obj):
        self.updateProps(obj)

    def updateProps(self, obj, useCase="Generic"):
        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "ExposedGeometry"
        
        if not hasattr(obj, "UseCase"):
            obj.addProperty("App::PropertyString", "UseCase", "ConstraintDesign", "Type of constraint design feature.")
            if useCase in useCases:
                obj.UseCase = useCase
        
        if not hasattr(obj, "Support"):
            obj.addProperty("App::PropertyString", "Support", "ConstraintDesign", "Element to expose.")
        
        if not hasattr(obj, "Missing"):
            obj.addProperty("App::PropertyBool", "Missing", "ConstraintDesign", "True if the exposed geometry is missing.")
        
        if not hasattr(obj, "IsSetup") and hasattr(obj, "UseCase") and obj.UseCase == "Sketch":
            obj.addProperty("App::PropertyBool", "IsSetup", "ConstraintDesign", "True if the exposed geometry is setup by the sketch.")
            obj.IsSetup = False
    
    def generateEquations(self):
        pass

    def generateParameters(self):
        pass

    def getConstrainedElements(self):
        pass

    def getContainer(self, obj):
        return super(ExposedGeo, self).getContainer(obj)
        
    def generateShape(self, obj, prevShape):
        self.updateProps(obj)

        shape = Part.Shape()
        container = self.getContainer(obj)
        elementName = None
        hashStr = obj.Support
        placement = App.Placement()
        obj.purgeTouched()
        isInSketch = False

        for item in obj.InList:
            if isType(item, "BoundarySketch"):
                isInSketch = True
                break

        if not isInSketch and hasattr(obj, "UseCase") and obj.UseCase == "Sketch" and hasattr(obj, "IsSetup") and obj.IsSetup:
            obj.Proxy = None
            obj.ViewObject.Proxy = None
            obj.Document.removeObject(obj.Name)
            return prevShape

        feature, elementName = getElementFromHash(container, obj.Support, requestingObjectLabel=obj.Label)

        if feature == None or elementName == None: # do not add error here, getElementFromHash already errors
            if hasattr(obj, "Missing"):
                obj.Missing = True
            if not obj.Label.startswith(missingStr):
                obj.Label = f"{missingStr}{obj.Label}"

            if hasattr(obj, "UseCase") and obj.UseCase == "Sketch":
                obj.ViewObject.ShowInTree = True
                obj.Visibility = True
            
            return obj.Shape
        else:
            if hasattr(obj, "Missing"):
                obj.Missing = False
                
            if obj.Label.startswith(missingStr):
                obj.Label = obj.Label.removeprefix("(MISSING) ")

            if hasattr(obj, "UseCase") and obj.UseCase == "Sketch":
                obj.ViewObject.ShowInTree = False
                obj.Visibility = False

        scoreDocument, scopeContainer, _, _ = getObjectsFromScope(container, hashStr)
        
        if elementName != None:
            element = feature.Shape.getElement(elementName).copy()
            if element != None:
                if isinstance(element, Part.Edge):
                    placement.Base = element.CenterOfMass
                elif isinstance(element, Part.Vertex):
                    placement.Base = element.Point

                element.applyTranslation(placement.Base * -1)
                shape = Part.Compound([element])

                # if scoreDocument.Name != container.Document.Name or scopeContainer.Name != container.Name:
                    # globalP = feature.getGlobalPlacement()

                    # print(globalP)

                    # placement.Base += globalP.Base
                    # placement.Rotation = globalP.Rotation

                obj.Shape = shape
        
        obj.ViewObject.Selectable = True
        obj.ViewObject.LineWidth = 4 
        obj.ViewObject.PointSize = 6
        obj.Placement = placement
        obj.purgeTouched()
        
        return shape
    
    # Format {"HashName": {"Edge:" edge, "GeoTag", sketchGeoTag}}

    def onChanged(self, obj, prop):
        print(f"exposed geo change: {prop}")

        if prop == "Visibility" \
                and obj.Visibility \
                and hasattr(obj, "UseCase") \
                and obj.UseCase == "Sketch" \
                and hasattr(obj, "Missing") \
                and not obj.Missing:
            obj.Visibility = False
            

    def getElement(self, obj, hash):
        return None, None

    def execute(self, obj):
        self.updateProps(obj)
    
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
    
    def dumps(self):
        return None
    
    def loads(self, state):
        return None

    def showGui(self, obj):
        Gui.Control.showDialog(ExposedGeoTaskPanel(obj))

class ViewProviderExposedGeo:
    def __init__(self, obj):
        obj.Proxy = self
        obj.Selectable = False
        self.Origin = None
    
    def onDelete(self, vobj, subelements):
        try:
            container = vobj.Object.Proxy.getContainer(vobj.Object)
            container.Proxy.fixTip(container)
        except Exception as e:
            App.Console.PrintWarning("Deleting Fillet Errored, reason: " + str(e))
        
        return True
    
    def attach(self, vobj):
        # Called when the view provider is attached
        self.Object = vobj
        self.Object.Selectable = True

        return

    def setEdit(self, vobj, mode):
        vobj.Object.Document.openTransaction("EditExposedGeo")
        vobj.Object.Proxy.showGui(vobj.Object)
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
        return os.path.join(os.path.dirname(__file__), "..", "icons", "ExposedGeo.svg")
    
    def claimChildren(self):
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
    
def makeExposedGeo(stringID = None, activeObject = None, useCase="Generic"):
    if activeObject == None:
        activeObject = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")

    if activeObject != None and hasattr(activeObject, "Type") and activeObject.Type == "PartContainer":
        doc = activeObject.Document
        doc.openTransaction("CreateExposedGeo")
        name = "ExposedGeo"

        if useCase == "Sketch":
            name = "ExternalSketchGeometry"

        obj = App.ActiveDocument.addObject("Part::FeaturePython", name)
        ExposedGeo(obj, useCase)
        ViewProviderExposedGeo(obj.ViewObject)

        if stringID == None:
            hashes = getIDsFromSelection(Gui.Selection.getCompleteSelection())
        else:
            hashes = [stringID]

        if type(hashes) == list and len(hashes) == 0:
            App.Console.PrintError("Unable to find string IDs from selection!")
            return None
        else:
            _, _, afterFeature, _ = getObjectsFromScope(activeObject, hashes[0])

            obj.Support = hashes[0]
            activeObject.Proxy.addObject(activeObject, obj, False, afterFeature)

            return obj
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")
        return None