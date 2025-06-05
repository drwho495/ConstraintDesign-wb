import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Entities.Derive import makeDerive

class CreateDerive:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "PartContainer.svg"),
            'MenuText': "Creates Derive Feature",
            'ToolTip': "Creates a new Derive feature"
        }
        
    def Activated(self):
        doc = FreeCAD.ActiveDocument
        if not doc:
            doc = FreeCAD.newDocument()
        
        # Only works if the gui is up
        if FreeCAD.GuiUp == True:
            makeDerive()
            
        doc.recompute()
        
    def IsActive(self):
        return True

FreeCADGui.addCommand('CreateDerive', CreateDerive())