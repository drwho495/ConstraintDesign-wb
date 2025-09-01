import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Entities.Pattern import makePattern

class CreateLinearPattern:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "LinearPattern.svg"),
            'MenuText': "Create Linear Pattern Feature",
            'ToolTip': "Creates a new Linear Pattern feature"
        }
        
    def Activated(self):
        doc = FreeCAD.ActiveDocument
        
        # Only works if the gui is up
        if FreeCAD.GuiUp == True:
            makePattern(0)
            
        doc.recompute()
        
    def IsActive(self):
        return FreeCAD.ActiveDocument != None

FreeCADGui.addCommand('CreateLinearPattern', CreateLinearPattern())