import FreeCAD as App
import FreeCADGui as Gui
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from Utils import Utils

class EditConstraintSketch:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "Sketch.svg"),
            'MenuText': "Edit Constraint Design Sketch Placement",
            'ToolTip': "Edit the selected Constraint Sketch using the task panel."
        }
        
    def Activated(self):
        if App.GuiUp == True:
            sel = Gui.Selection.getSelection()

            if sel and hasattr(sel[0], 'Proxy') and hasattr(sel[0].Proxy, 'showGui') and Utils.isType(sel[0], "BoundarySketch"):
                sel[0].Proxy.showGui(sel[0])
            else:
                App.Console.PrintError("Please select a viable ConstraintSketch to edit.\n")
        
    def IsActive(self):
        return App.ActiveDocument != None

Gui.addCommand('EditConstraintSketch', EditConstraintSketch())
