# This file initializes the graphical user interface components of the addon.

from PySide import QtGui
import FreeCAD
import FreeCADGui

class MyAddonGui:
    def __init__(self):
        self.toolbar = FreeCADGui.getMainWindow().findChild(QtGui.QToolBar, "MyAddonToolbar")
        if not self.toolbar:
            self.toolbar = FreeCADGui.getMainWindow().addToolBar("MyAddonToolbar")
        
        self.addToolbarButton()

    def addToolbarButton(self):
        icon = QtGui.QIcon(FreeCAD.getResourceDir() + "path/to/icon.svg")
        action = QtGui.QAction(icon, "My Addon Action", FreeCADGui.getMainWindow())
        action.triggered.connect(self.onButtonClick)
        self.toolbar.addAction(action)

    def onButtonClick(self):
        FreeCAD.Console.PrintMessage("My Addon button clicked!\n")

def initializeGui():
    MyAddonGui()

def unloadGui():
    FreeCADGui.getMainWindow().findChild(QtGui.QToolBar, "MyAddonToolbar").deleteLater()