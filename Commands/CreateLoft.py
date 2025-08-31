import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Entities.Loft import makeLoft

class CreateLoft:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "Loft.svg"),
            'MenuText': "Create Loft Feature",
            'ToolTip': "Creates a new Loft feature"
        }
        
    def Activated(self):
        doc = FreeCAD.ActiveDocument
        if not doc:
            doc = FreeCAD.newDocument()
        
        # Only works if the gui is up
        if FreeCAD.GuiUp == True:
            makeLoft()
            
        doc.recompute()
        
    def IsActive(self):
        return FreeCAD.ActiveDocument != None

FreeCADGui.addCommand('CreateLoft', CreateLoft())