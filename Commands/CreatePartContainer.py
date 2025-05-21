
import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from PartContainer import *

class CreatePartContainer:
    """Command to create a PartContainer feature"""
    
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "CreateConstraintPart.svg"),
            'MenuText': "Create Part Container",
            'ToolTip': "Creates a new Part Container feature"
        }
        
    def Activated(self):
        doc = FreeCAD.ActiveDocument
        if not doc:
            doc = FreeCAD.newDocument()
        
        # Only works if the gui is up
        if FreeCAD.GuiUp == True:
            makePartContainer()
            
        doc.recompute()
        
    def IsActive(self):
        return True

FreeCADGui.addCommand('CreatePartContainer', CreatePartContainer())