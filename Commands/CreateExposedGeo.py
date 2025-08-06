import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Entities.ExposedGeo import makeExposedGeo

class CreateExposedGeo:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "ExposedGeo.svg"),
            'MenuText': "Create Exposed Geometry datum.",
            'ToolTip': "Creates a new Exposed Geometry datum."
        }
        
    def Activated(self):
        if FreeCAD.GuiUp == True:
            makeExposedGeo(canMakeMultiple = True)
        
    def IsActive(self):
        return FreeCAD.ActiveDocument != None

FreeCADGui.addCommand('CreateExposedGeo', CreateExposedGeo())