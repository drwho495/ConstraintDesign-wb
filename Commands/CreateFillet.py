import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Entities.Dressup import makeDressup

class CreateFillet:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "PartContainer.svg"),
            'MenuText': "Create Fillet Feature",
            'ToolTip': "Creates a new Fillet feature"
        }
        
    def Activated(self):
        # Only works if the gui is up
        if FreeCAD.GuiUp == True:
            makeDressup(0)
            
    def IsActive(self):
        return True

FreeCADGui.addCommand('CreateFillet', CreateFillet())