import FreeCAD as App
import FreeCADGui as Gui
from pivy import coin
import Part
import sys
import math
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from Utils.Utils import getIDsFromSelection, getElementFromHash
from Utils.GuiUtils import SelectorWidget
from Utils.Constants import *
from PySide import QtWidgets
import json
from Entities.Entity import Entity

useCases = ["Generic", "Assembly"]

class JointTaskPanel:
    def __init__(self, obj, addOldSelection=True, startSelection=[]):
        self.form = QtWidgets.QWidget()
        self.form.destroyed.connect(self.close) # run immediatly incase something else errors

        layout = QtWidgets.QVBoxLayout(self.form)
        layout.addWidget(QtWidgets.QLabel("Editing: " + obj.Label))
        self.joint = obj

        button_layout = QtWidgets.QHBoxLayout()

        self.applyButton = QtWidgets.QPushButton("Apply")
        self.updateButton = QtWidgets.QPushButton("Update")
        self.cancelButton = QtWidgets.QPushButton("Cancel")

        button_layout.addWidget(self.applyButton)
        button_layout.addWidget(self.updateButton)
        button_layout.addWidget(self.cancelButton)

        layout.addLayout(button_layout)
        
        self.applyButton.clicked.connect(self.accept)
        self.updateButton.clicked.connect(self.update)
        self.cancelButton.clicked.connect(self.reject)

        self.oldSupport = obj.Support

        self.mapModeEnumerationLayout = QtWidgets.QHBoxLayout()
        self.mapModeLabel = QtWidgets.QLabel("MapMode:")
        self.mapModeEnumeration = QtWidgets.QComboBox()
        self.mapModeEnumeration.setEditable(True)
        self.mapModeEnumerationLayout.addWidget(self.mapModeLabel)
        self.mapModeEnumerationLayout.addWidget(self.mapModeEnumeration)
        self.mapModeEnumerationLayout.setContentsMargins(0, 5, 0, 0)

        self.oldMapMode = obj.MapMode
        self.selectedType = self.oldMapMode

        self.updateEnumeration()

        self.container = self.joint.Proxy.getContainer(self.joint)
        self.selector = SelectorWidget(addOldSelection = addOldSelection, startSelection = startSelection, container = self.container)
        self.selector.selectionChanged.connect(self.selectionChanged)
        layout.addWidget(self.selector)
        layout.addLayout(self.mapModeEnumerationLayout)
        self.mapModeEnumeration.currentIndexChanged.connect(self.enumerationChanged)
    
    def selectionChanged(self, newSelection = []):
        self.update()

    def enumerationChanged(self, index):
        newType = self.mapModeEnumeration.itemData(index)

        self.selectedType = newType

        self.update()

    def updateEnumeration(self):
        enums = self.joint.getEnumerationsOfProperty("MapMode")

        for type in enums:
            self.mapModeEnumeration.addItem(type, type)
        
        self.mapModeEnumeration.setCurrentIndex(enums.index(self.selectedType))

    def update(self):
        selected = self.selector.getSelection()

        print(selected)
        print(self.selectedType)

        self.joint.Support = selected
        self.joint.MapMode = self.selectedType # needed because some logic in the proxy causes the enum selection to be overrided
        self.joint.Proxy.execute(self.joint)

        self.updateEnumeration()

    def close(self):
        self.selector.cleanup()

        Gui.Control.closeDialog()
    
    def accept(self):
        self.update()
        self.close()

    def reject(self):
        print("reject joint")
        self.joint.Proxy.execute(self.joint)

        print(f"old: {self.oldSupport}")

        self.joint.Support = self.oldSupport
        self.joint.MapMode = self.oldMapMode

        self.joint.Proxy.execute(self.joint)

        self.close()
    
    def getStandardButtons(self):
        return 0

    def getTitle(self):
        return "Dressup Task Panel"

    def IsModal(self):
        return False

class FeatureJoint(Entity):
    def __init__(self, obj, useCase = "Generic"):
        obj.Proxy = self
        self.updateProps(obj, useCase)
    
    def showGui(self, obj):
        Gui.Control.showDialog(JointTaskPanel(obj, False, obj.Support))
    
    def updateProps(self, obj, useCase = "Generic"):
        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "Joint"
        
        if not hasattr(obj, "UseCase"):
            obj.addProperty("App::PropertyString", "UseCase", "ConstraintDesign", "Type of constraint design feature.")
            if useCase in useCases:
                obj.UseCase = useCase
            else:
                obj.UseCase = "Generic"

        if not obj.hasExtension("Part::AttachExtensionPython"):
            obj.addExtension("Part::AttachExtensionPython")

        if not hasattr(obj, "Support"):
            obj.addProperty("App::PropertyStringList", "Support", "ConstraintDesign")
        
        if not hasattr(obj, "SupportType"):
            obj.addProperty("App::PropertyEnumeration", "SupportType", "ConstraintDesign")
            obj.SupportType = ["Deactivated"]
        
        if hasattr(obj, "AttachmentSupport"):
            obj.setEditorMode("AttachmentSupport", 2)

        if hasattr(obj, "AttacherEngine"):
            obj.setEditorMode("AttacherEngine", 2)

        if hasattr(obj, "MapMode"):
            obj.setEditorMode("MapMode", 2)
    
    def generateEquations(self):
        pass

    def generateParameters(self):
        pass

    def getConstrainedElements(self):
        pass

    def getContainer(self, obj):
        return super(FeatureJoint, self).getContainer(obj)
    
    def generateShape(self, obj, prevShape):
        self.execute(obj)
    # Format {"HashName": {"Edge:" edge, "GeoTag", sketchGeoTag}}
    def execute(self, obj):
        self.updateAttachmentProperties(obj)
        obj.positionBySupport()

        obj.purgeTouched()

    def updateAttachmentProperties(self, obj):
        self.updateProps(obj)
        container = self.getContainer(obj)
        elementSupport = []

        if obj.SupportType not in obj.getEnumerationsOfProperty("MapMode"):
            obj.SupportType = "Deactivated"
            App.Console.PrintWarning(f"Support Type in {obj.Label} is invalid.")

        obj.MapMode = obj.SupportType

        if container != None:
            elements = getElementFromHash(container, obj.Support, asList=True, requestingObjectLabel=obj.Label)

            for fullElement in elements:
                if fullElement[0] != None and fullElement[1] != None and len(fullElement) < 4:
                    elementSupport.append(fullElement)
            
            obj.AttachmentSupport = elementSupport
        else:
            App.Console.PrintError(f"{obj.Label} needs to be put into a suitable part container!\n")
        
        obj.SupportType = obj.getEnumerationsOfProperty("MapMode")
            
    def onChanged(self, obj, prop):
        pass
            
    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

class ViewProviderJoint:
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

    def makeJointShape(self):
        root = coin.SoSeparator()

        # Colors
        red = (1.0, 0.0, 0.0)
        green = (0.0, 1.0, 0.0)
        blue = (0.0, 0.0, 1.0)
        circleColorRGB = (1.0, 1.0, 1.0)

        lightModel = coin.SoLightModel()
        lightModel.model = coin.SoLightModel.BASE_COLOR
        root.addChild(lightModel)

        # Line width
        draw_style = coin.SoDrawStyle()
        draw_style.lineWidth = 3  # <-- Line thickness here
        root.addChild(draw_style)


        circleSep = coin.SoSeparator()
        circleColor = coin.SoBaseColor()
        circleColor.rgb = circleColorRGB
        circleCoords = coin.SoCoordinate3()
        circleFaceset = coin.SoFaceSet()

        radius = 6.0
        segments = 32
        points = [(0, 0, 0)]

        for i in range(segments + 1):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            z = 0
            points.append((x, y, z))

        circleCoords.point.setValues(0, len(points), points)
        circleFaceset.numVertices = len(points)

        circleSep.addChild(circleColor)
        circleSep.addChild(circleCoords)
        circleSep.addChild(circleFaceset)
        root.addChild(circleSep)

        def createArrow(color, axis, length=10):
            sep = coin.SoSeparator()

            colorNode = coin.SoBaseColor()
            colorNode.rgb = color
            sep.addChild(colorNode)

            coords = coin.SoCoordinate3()
            if axis == 'x':
                coords.point.setValues(0, 4, [(0, 0, 0), (length, 0, 0)])
            elif axis == 'y':
                coords.point.setValues(0, 4, [(0, 0, 0), (0, length, 0)])
            elif axis == 'z':
                coords.point.setValues(0, 4, [(0, 0, 0), (0, 0, length)])

            line = coin.SoLineSet()
            line.numVertices = 2

            sep.addChild(coords)
            sep.addChild(line)

            return sep

        root.addChild(createArrow(red, 'x'))
        root.addChild(createArrow(green, 'y'))
        root.addChild(createArrow(blue, 'z', 5))

        return root
    
    
    def attach(self, vobj):
        # Called when the view provider is attached
        self.Object = vobj
        self.Object.Selectable = False

        self.root = coin.SoSeparator()
        self.lcsNode = self.makeJointShape()
        self.root.addChild(self.lcsNode)
        vobj.addDisplayMode(self.root, "LCS")

        return

    def setEdit(self, vobj, mode):
        vobj.Object.Document.openTransaction("EditJoimt")
        vobj.Object.Proxy.showGui(vobj.Object)

        return False

    def unsetEdit(self, vobj, mode):
        return True

    def updateData(self, fp, prop):
        # Called when a property changes
        return

    def getDisplayModes(self, vobj):
        # Available display modes
        return ["LCS"]

    def getDefaultDisplayMode(self):
        # Default display mode
        return "LCS"

    def setDisplayMode(self, mode):
        # Called when the display mode changes
        return mode

    def onChanged(self, vobj, prop):
        # Called when a property of the viewobject changes
        return

    def getIcon(self):
        return os.path.join(os.path.dirname(__file__), "..", "icons", "Joint.svg")
    
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

def makeBoundary(document):
    boundary = document.addObject("Part::Feature", "Boundary")
    boundary.addProperty("App::PropertyString", "Type")
    boundary.Type = "Boundary"

    return boundary

""" Method to create a FeatureDressup. """
def makeJoint(useCase = "Generic"):
    activeObject = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")

    if activeObject != None and hasattr(activeObject, "Type") and activeObject.Type == "PartContainer":
        doc = activeObject.Document
        doc.openTransaction("CreateJoint")

        obj = App.ActiveDocument.addObject("Part::FeaturePython", "Joint")
        FeatureJoint(obj, useCase)
        ViewProviderJoint(obj.ViewObject)

        hashes = getIDsFromSelection(Gui.Selection.getCompleteSelection())

        activeObject.Proxy.addObject(activeObject, obj, True)
        # obj.Proxy.showGui(obj, True)

        obj.Support = hashes
        activeObject.recompute()
    else:
        App.Console.PrintError("Active object is not a PartContainer!\n")