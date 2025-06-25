import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Utils import getParent, isType, featureTypes, boundaryTypes, datumTypes

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

        print("move: " + str(self.direction))

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

                        print(obj.Label)

                    parent.Group = group
                else:
                    print("obj: " + selectedObj.Label + " not in group!")
            else:
                print("unable to find parent or group")
        else:
            print("Selection is none")
            
    def IsActive(self):
        return True

FreeCADGui.addCommand('MoveDesignObjectUp', MoveDesignObject(1))
FreeCADGui.addCommand('MoveDesignObjectDown', MoveDesignObject(-1))