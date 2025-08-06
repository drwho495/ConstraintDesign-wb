import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Entities.Dressup import makeDressup

class CreateChamfer:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "Chamfer.svg"),
            'MenuText': "Create Chamfer Feature",
            'ToolTip': "Creates a new Chamfer feature"
        }
        
    def Activated(self):
        if FreeCAD.GuiUp == True:
            makeDressup(1)
        
    def IsActive(self):
        return FreeCAD.ActiveDocument != None

FreeCADGui.addCommand('CreateChamfer', CreateChamfer())