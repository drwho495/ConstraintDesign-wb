# import FreeCAD as App
# import FreeCADGui as Gui
# import Part
# import sys
# import os
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
# from Utils import isType, getParent, featureTypes, boundaryTypes, getIDsFromSelection, getObjectsFromScope, getElementFromHash
# from Entities.Entity import Entity
# import SketcherGui

# class BoundarySketch:
#     def __init__(self, obj):
#         obj.Proxy = self
#         self.updateProps(obj)

#     def updateProps(self, obj):
#         if not hasattr(obj, "Type"):
#             obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
#             obj.Type = "BoundarySketch"
        
#         if not hasattr(obj, "Support"):
#             obj.addProperty("App::PropertyStringList", "Support", "Base")
        
#         obj.setEditorMode("AttacherEngine", 3)
#         obj.setEditorMode("AttachmentSupport", 3)
#         obj.setEditorMode("MapMode", 3)
    
#     # def getContainer(self, obj):
#         # return super(BoundarySketch, self).getContainer(obj)
               
#     def execute(self, obj):
#         self.updateProps(obj)

#         print(obj.Label + " updated!")
            
#     def onChanged(self, obj, prop):
#         pass
    
#     def __getstate__(self):
#         return None

#     def __setstate__(self, state):
#         return None

# class ViewProviderBoundarySketch():
#     def positionSketch(self, sketch, container):
#         if hasattr(sketch, "Support"):
#             support = sketch.Support
#             vectors = []

#             for hash in support:
#                 object, elementName = getElementFromHash(container, hash)
#                 element = object.Shape.getElement(elementName)

#                 if type(element).__name__ == "Edge":
#                     if len(element.Vertexes) == 2:
#                         vectors.append(element.Vertexes[0].Point)
#                         vectors.append(element.Vertexes[1].Point)
#                     else:
#                         for vertex in element.Vertexes:
#                             vectors.append(vertex.Point)
#                 elif type(element).__name__ == "Vertex":
#                     vectors.append(element.Point)

#             if len(vectors) >= 3:
#                 p1 = vectors[0]
#                 p2 = vectors[1]
#                 p3 = vectors[2]

#                 x_axis = (p2 - p1).normalize()
#                 normal = (p2 - p1).cross(p3 - p1).normalize()
#                 y_axis = normal.cross(x_axis)

#                 rot = App.Rotation(x_axis, y_axis, normal)
#                 translation = p1 - rot.multVec(App.Vector(0, 0, 0))

#                 sketch.Placement = App.Placement(translation, rot)
    
#     # def setEdit(self, vobj, mode):
#         # print("Edit " + vobj.Object.Label)

#     # def unsetEdit(self, vobj, mode):
#         # print("Stop editing " + vobj.Object.Label)

#         # vobj.Object.ViewObject.TempoVis.restore()

#         # return True
    
# def makeSketch():
#     activeObject = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")

#     if activeObject is not None and hasattr(activeObject, "Type") and activeObject.Type == "PartContainer":
#         # hashes = getIDsFromSelection(Gui.Selection.getCompleteSelection())
        
#         newSketch = activeObject.Document.addObject("Sketcher::SketchObjectPython", "BoundarySketch")

#         BoundarySketch(newSketch)
#         # ViewProviderBoundarySketch(newSketch.ViewObject)
#         newSketch.ViewObject.Proxy = SketcherGui.ViewProviderSketchGeometryExtension

#         # newSketch.Support = hashes
#         activeObject.Proxy.addObject(activeObject, newSketch)

#         # positionSketch(newSketch, activeObject)
#     else:
#         Gui.Console.PrintError("You need to select a part container as your active object!\n")