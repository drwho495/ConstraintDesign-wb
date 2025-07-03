# import FreeCAD as App
# import FreeCADGui as Gui
# import sys
# import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
# from Utils.Utils import isType, getParent

# class UpdateSketchVisibility:
#     def GetResources(self):
#         return {
#             'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "Sketch.svg"),
#             'MenuText': "Fixes the visibility of a Part Container for a sketch",
#             'ToolTip': "Fixes the visibility of a Part Container for a sketch"
#         }
        
#     def Activated(self):
#         edit = Gui.ActiveDocument.getInEdit()

#         if edit != None:
#             editObject = edit.Object

#             if isType(editObject, "BoundarySketch"):
#                 container = getParent(container, "PartContainer")

#                 if container != None:
#                     container.Proxy.updateSupportVisibility(container, editObject, False)
        
#     def IsActive(self):
#         return True

# Gui.addCommand('UpdateSketchVisibility', UpdateSketchVisibility())