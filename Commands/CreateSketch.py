import FreeCAD as App
import FreeCADGui as Gui
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from Utils import Utils
from Entities.ConstraintSketch import makeSketch

class CreateConstraintSketch:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "Sketch.svg"),
            'MenuText': "Create a Sketch",
            'ToolTip': "Creates a new Sketch with a hasher or plane attachment"
        }
        
    def Activated(self):
        selection = Gui.Selection.getCompleteSelection()
        elements = Utils.getIDsFromSelection(selection)

        if App.GuiUp == True:
            makeSketch(elements)
        
    def IsActive(self):
        return App.ActiveDocument != None

Gui.addCommand('CreateConstraintSketch', CreateConstraintSketch())