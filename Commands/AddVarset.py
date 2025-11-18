import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Utils import Utils

class AddVarset:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "AddVarSet.svg"),
            'MenuText': "Adds a VarSet to a selected Part Container.",
            'ToolTip': "Adds a VarSet to a selected Part Container."
        }
        
    def Activated(self):
        selection = FreeCADGui.Selection.getSelection()

        if len(selection) == 1:
            selObj = selection[0]

            if Utils.isType(selObj, "PartContainer"):
                if not hasattr(selObj, "VariableContainer"):
                    selObj.Proxy.updateProps(selObj)

                varSet = selObj.Document.addObject("App::VarSet", "VarSet")
                varSet.Label = f"{selObj.Label}'s VarSet"

                selObj.Proxy.addObject(selObj, varSet, index = 0)
                selObj.VariableContainer = varSet
            else:
                FreeCAD.Console.PrintError("The selected object is not a part container!")
        else:
            FreeCAD.Console.PrintError("Please select only a single part container!")
        
    def IsActive(self):
        return FreeCAD.ActiveDocument != None

FreeCADGui.addCommand('AddVarset', AddVarset())