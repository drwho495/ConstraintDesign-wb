import os
import sys
import locater
from Commands.CreatePartContainer import CreatePartContainer  # Add this import
from Commands.CreateExtrusion import CreateExtrusion
from Commands.CreateLinearPattern import CreateLinearPattern
from Commands.CreatePartMirror import CreatePartMirror
from Commands.CreateFillet import CreateFillet
from Commands.CreateChamfer import CreateChamfer
from Commands.CreateCountersink import CreateCountersink
from Commands.CreateLoft import CreateLoft
from Commands.CreateDerive import CreateDerive
from Commands.CreateExposedGeo import CreateExposedGeo
from Commands.MoveFeatureCommands import MoveDesignObject
from Commands.CreateSketch import CreateConstraintSketch
from GuiUtils import SelectorWidget
import Grid.GridManager as GridManager
import FreeCAD as App
import FreeCADGui as Gui

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(locater.__file__)))) # allow python to see ".."

__dirname__ = os.path.dirname(locater.__file__)

class GridDocumentObserver:
    def slotCreatedDocument(self, doc):
        if isinstance(Gui.activeWorkbench(), ConstraintDesign):
            GridManager.addGrid(doc)

    def slotLoadedDocument(self, doc):
        if isinstance(Gui.activeWorkbench(), ConstraintDesign):
            GridManager.addGrid(doc)

    def slotDeletedDocument(self, doc):
        GridManager.removeDocument(doc)

class ConstraintDesign(Gui.Workbench):
    global __dirname__

    MenuText = App.Qt.translate("Workbench", "Constraint Design")
    ToolTip = App.Qt.translate("Workbench", "Constraint Design Workbench")
    Icon = os.path.join(__dirname__, "icons", "ConstraintPart.svg")

    App.Console.PrintLog(Icon)

    commands = [
    ]
    def __init__(self):
        self.documentObserver = None

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        """
        Initialize the workbench commands
        """
        # List the commands to be added to the workbench
        mainCommands = [
            'CreatePartContainer'
        ]

        featureCommands = [
            'CreateExtrusion',
            'CreatePartMirror',
            'CreateDerive',
            'CreateLinearPattern',
            'CreateLoft'
        ]

        dressupCommands = [
            'CreateFillet',
            'CreateChamfer',
            'CreateCountersink'
        ]

        treeCommands = [
            "MoveDesignObjectUp",
            "MoveDesignObjectDown"
        ]

        sketchCommands = [
            'CreateConstraintSketch'
        ]

        datumCommands = [
            'CreateExposedGeo'
        ]
        
        # Register the commands
        self.appendToolbar("Part Container", mainCommands)
        self.appendMenu("Part Container", mainCommands)

        self.appendToolbar("Features", featureCommands)
        self.appendMenu("Features", featureCommands)

        self.appendToolbar("Dressups", dressupCommands)
        self.appendMenu("Dressups", dressupCommands)

        self.appendToolbar("Tree Commands", treeCommands)
        self.appendMenu("Tree Commands", treeCommands)

        self.appendToolbar("Sketch Commands", sketchCommands)
        self.appendMenu("Sketch Commands", sketchCommands)

        self.appendToolbar("Datum Commands", datumCommands)
        self.appendMenu("Datum Commands", datumCommands)

    def Activated(self):
        GridManager.showAllGrids()

        if App.ActiveDocument != None:
            GridManager.addGrid(App.ActiveDocument)

        self.documentObserver = GridDocumentObserver()

        App.addDocumentObserver(self.documentObserver)

    def Deactivated(self):
        if self.documentObserver != None:
            App.removeDocumentObserver(self.documentObserver)
        
        GridManager.hideAllGrids()