import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Entities.Dressup import makeDressup

class CreateCountersink:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "Countersink.svg"),
            'MenuText': "Create Countersink Feature",
            'ToolTip': "Creates a new Countersink feature"
        }
        
    def Activated(self):
        if FreeCAD.GuiUp == True:
            makeDressup(2)
        
    def IsActive(self):
        return FreeCAD.ActiveDocument != None

FreeCADGui.addCommand('CreateCountersink', CreateCountersink())