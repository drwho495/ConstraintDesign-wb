import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Entities.ExposedGeo import makeExposedGeo

class CreateExposedGeo:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "PartContainer.svg"),
            'MenuText': "Create Exposed Geometry datum.",
            'ToolTip': "Creates a new Exposed Geometry datum."
        }
        
    def Activated(self):
        doc = FreeCAD.ActiveDocument
        if not doc:
            doc = FreeCAD.newDocument()
        
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
            makeExposedGeo(elements)
            
        doc.recompute()
        
    def IsActive(self):
        return True

FreeCADGui.addCommand('CreateExposedGeo', CreateExposedGeo())