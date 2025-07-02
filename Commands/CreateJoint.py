import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Entities.Joint import makeJoint

class CreateJoint:
    def GetResources(self):
        return {
            "Pixmap": os.path.join(os.path.dirname(__file__), "..", "icons", "Joint.svg"),
            "MenuText": "Create Joint datum entity.",
            "ToolTip": "Creates a new Joint datum entity."
        }
        
    def Activated(self):
        # Only works if the gui is up
        if FreeCAD.GuiUp == True:
            makeJoint()
            
    def IsActive(self):
        return True

FreeCADGui.addCommand("CD_CreateJoint", CreateJoint()) # Add CD_ prefix to avoid clash with Assembly