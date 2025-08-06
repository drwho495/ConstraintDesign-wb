import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Utils.Utils import getParent, isType
from Utils.Constants import *

class MoveDesignObject:
    def __init__(self, dir):
        self.direction = dir

    def GetResources(self):
        if self.direction == 1:
            return {
                'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "Up.svg"),
                'MenuText': "Move Selected Object up.",
                'ToolTip': "Moves Selected Object up the Tree View"
            }
        elif self.direction == -1:
            return {
                'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "Down.svg"),
                'MenuText': "Move Selected Object down.",
                'ToolTip': "Moves Selected Object down the Tree View"
            }
        
    def Activated(self):
        selection = FreeCADGui.Selection.getSelection()

        if len(selection) != 0:
            selectedObj = selection[0]
            parent = getParent(selectedObj, "PartContainer")

            types = featureTypes.copy()
            types.extend(datumTypes)

            if parent != None and isType(selectedObj, types) and hasattr(parent, "Group"):
                group = parent.Group

                if selectedObj in group:
                    index = group.index(selectedObj)
                    objects = [selectedObj]

                    if hasattr(selectedObj, "Group"):
                        objects.extend(objects)

                    for obj in objects:
                        group.remove(obj)
                        group.insert(index + (-1 * self.direction), obj)

                    parent.Group = group
            
    def IsActive(self):
        return FreeCAD.ActiveDocument != None

FreeCADGui.addCommand('MoveDesignObjectUp', MoveDesignObject(1))
FreeCADGui.addCommand('MoveDesignObjectDown', MoveDesignObject(-1))