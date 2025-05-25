import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Entities.PartMirror import makePartMirror

class CreatePartMirror:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "PartContainer.svg"),
            'MenuText': "Creates Part Mirror Feature",
            'ToolTip': "Creates a new Part Mirror feature"
        }
        
    def Activated(self):
        doc = FreeCAD.ActiveDocument
        if not doc:
            doc = FreeCAD.newDocument()
        
        # Only works if the gui is up
        if FreeCAD.GuiUp == True:
            makePartMirror()
            
        doc.recompute()
        
    def IsActive(self):
        return True

FreeCADGui.addCommand('CreatePartMirror', CreatePartMirror())