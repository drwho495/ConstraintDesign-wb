import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Entities.Dressup import makeDressup

class CreateChamfer:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "PartContainer.svg"),
            'MenuText': "Create Chamfer Feature",
            'ToolTip': "Creates a new Chamfer feature"
        }
        
    def Activated(self):
        selection = FreeCADGui.Selection.getCompleteSelection()
        elements = []
        for obj in selection:
            if obj.HasSubObjects:
                elements.append((obj.Object, obj.SubElementNames[0]))

        if len(elements) == 0:
            FreeCAD.Console.PrintError("You must select at least one edge!\n")
            return
        
        # Only works if the gui is up
        if FreeCAD.GuiUp == True:
            makeDressup(elements, 1)
        
    def IsActive(self):
        return True

FreeCADGui.addCommand('CreateChamfer', CreateChamfer())