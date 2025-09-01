
import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from PartContainer import *
from Utils import Utils

class CreateConstraintLink:
    """Command to create a ConstraintLink feature"""
    
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "ConstraintLinkPart.svg"),
            'MenuText': "Create Constraint Link",
            'ToolTip': "Creates a new Constraint Link"
        }
        
    def Activated(self):
        if FreeCAD.GuiUp == True:
            sel = Gui.Selection.getCompleteSelection()

            if len(sel) != 0 and hasattr(sel[0], "Object") and sel[0].Object != None:
                selectedObj = sel[0].Object

                if Utils.isType(selectedObj, "PartContainer"):
                    makePartContainer(selectedObj)
                else:
                    App.Console.PrintError("The object you selected was not a ConstraintDesign part container!\n")
            else:
                App.Console.PrintError("You need to select a Part Container object to link!\n")
        
    def IsActive(self):
        return FreeCAD.ActiveDocument != None

FreeCADGui.addCommand('CreateConstraintLink', CreateConstraintLink())