import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Entities.GuiConstraint import makeGuiConstraint

class CreateCoincidentConstraint:
    """Command to create a Coincident Constraint"""
    
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "PartContainer.svg"),
            'MenuText': "Create Coincident Constraint",
            'ToolTip': "Creates a new Coincident Constraint"
        }
        
    def Activated(self):
        doc = FreeCAD.ActiveDocument
        if not doc:
            # doc = FreeCAD.newDocument()
            FreeCAD.Console.PrintError("No document found!\n")
            return
        # Only works if the gui is up
        if FreeCAD.GuiUp == True:
            selection = FreeCADGui.Selection.getCompleteSelection()
            
            elements = []
            for obj in selection:
                if obj.HasSubObjects:
                    elements.append((obj.Object, obj.SubElementNames[0]))

            if len(elements) != 2:
                FreeCAD.Console.PrintError("Please select 2 objects!\n")
                return

            makeGuiConstraint("Coincident", elements)
            
        doc.recompute()
        
    def IsActive(self):
        return True

FreeCADGui.addCommand('CreateCoincidentConstraint', CreateCoincidentConstraint())