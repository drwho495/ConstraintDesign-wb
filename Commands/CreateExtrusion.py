import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Entities.Extrusion import makeExtrusion

class CreateExtrusion:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "Extrusion.svg"),
            'MenuText': "Create Extrusion Feature",
            'ToolTip': "Creates a new Extrusion feature"
        }
        
    def Activated(self):
        doc = FreeCAD.ActiveDocument
        if not doc:
            doc = FreeCAD.newDocument()
        
        # Only works if the gui is up
        if FreeCAD.GuiUp == True:
            makeExtrusion()
            
        doc.recompute()
        
    def IsActive(self):
        return FreeCAD.ActiveDocument != None

FreeCADGui.addCommand('CreateExtrusion', CreateExtrusion())