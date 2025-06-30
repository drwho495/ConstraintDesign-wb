import os
import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide import QtGui
from Utils import getElementFromHash, getIDsFromSelection, getStringID, getParent, isType
from Entities.ExposedGeo import makeExposedGeo
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."

# def updateSketch(sketch, container):
    # for item in sketch.OutList:
        # print(f"dependency: {item.Label}")
        # if isType(item, "ExposedGeometry"):
            # item.Proxy.generateShape(item, Part.Shape())
# 
    # positionSketch(sketch, container)
    # sketch.recompute()

# def positionSketch(sketch, container):
#     if hasattr(sketch, "Support") and not hasattr(sketch, "SupportHashes"):
#         sketch.addProperty("App::PropertyStringList", "SupportHashes", "Base")
#         sketch.SupportHashes = sketch.Support

#         sketch.removeProperty("Support")

#     if not hasattr(sketch, "SupportPlane"): 
#         sketch.addProperty("App::PropertyXLink", "SupportPlane", "Base")
    
#     if not hasattr(sketch, "SupportType"): 
#         sketch.addProperty("App::PropertyEnumeration", "SupportType", "Base")
#         sketch.SupportType = ["Plane", "Hashes"]
#         sketch.SupportType = "Hashes"
    
#     if hasattr(sketch, "SupportType") and hasattr(sketch, "SupportPlane") and hasattr(sketch, "SupportHashes"):
#         if sketch.SupportType == "Hashes":
#             vectors = []

#             for hash in sketch.SupportHashes:
#                 boundary, elementName = getElementFromHash(container, hash)
#                 element = boundary.Shape.getElement(elementName)

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
#         elif sketch.SupportType == "Plane":
#             sketch.Placement = sketch.SupportPlane.Placement

def makeSketch(hashes):
    activeObject = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")

    if activeObject is not None and hasattr(activeObject, "Type") and activeObject.Type == "PartContainer":
        newSketch = activeObject.Document.addObject("Sketcher::SketchObject", "Sketch")
        activeObject.Proxy.addObject(activeObject, newSketch)

        newSketch.setEditorMode("AttacherEngine", 3)
        newSketch.setEditorMode("AttachmentSupport", 3)
        newSketch.setEditorMode("MapMode", 3)

        newSketch.addProperty("App::PropertyStringList", "SupportHashes", "Base")
        newSketch.addProperty("App::PropertyXLink", "SupportPlane", "Base")
        newSketch.addProperty("App::PropertyString", "Type", "Base")
        newSketch.addProperty("App::PropertyEnumeration", "SupportType", "Base")

        newSketch.Type = "BoundarySketch"
        newSketch.SupportType = ["Plane", "Hashes"]
        if len(hashes) != 0:
            newSketch.SupportType = "Hashes"
            newSketch.SupportHashes = hashes
        else:
            newSketch.SupportType = "Plane"
            newSketch.SupportPlane = activeObject.Origin.OutList[3]


        positionSketch(newSketch, activeObject)
    else:
        App.Console.PrintError("You need to select a part container as your active object!\n")

# class CreateSketch:
#     def GetResources(self):
#         return {
#             'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "PartContainer.svg"),
#             'MenuText': "Create a Sketch",
#             'ToolTip': "Creates a new Sketch with a hasher attachement"
#         }
        
#     def Activated(self):
#         selection = Gui.Selection.getCompleteSelection()
#         elements = getIDsFromSelection(selection)

#         if App.GuiUp == True:
#             makeSketch(elements)
        
#     def IsActive(self):
#         return True

# Gui.addCommand('CreateSketch', CreateSketch())

# def addStringIDExternalGeo(stringID, sketch, container = None):
#     if container == None:
#         container = getParent(sketch, "PartContainer")
    
#     exposedGeo = makeExposedGeo(stringID, container)
#     exposedGeo.Proxy.generateShape(exposedGeo, Part.Shape())
#     exposedGeo.ViewObject.ShowInTree = False
#     exposedGeo.Visibility = False
#     elementName = ""

#     if len(exposedGeo.Shape.Edges) == 0:
#         if len(exposedGeo.Shape.Vertexes) != 0:
#             elementName = "Vertex1"
#     else:
#         elementName = "Edge1"
    
#     sketch.addExternal(exposedGeo.Name, elementName, True, False)

# class ExternalGeoSelector:
#     def __init__(self, sketch):
#         Gui.Selection.addObserver(self)
#         self.sketch = sketch
    
#     def cleanup(self):
#         Gui.Selection.removeObserver(self)

#     def addSelection(self, documentName, objectName, elementName, _):
#         document = App.getDocument(documentName)
#         edit = Gui.ActiveDocument.getInEdit()

#         if edit == None or edit.Object != self.sketch:
#             self.cleanup()
#             return

#         try:
#             if document != None and objectName != None:
#                 object = document.getObject(objectName)
#                 if object != None:
#                     container = getParent(self.sketch, "PartContainer")
#                     if container != None:
#                         stringId = getStringID(container, (object, elementName))

#                         print(stringId)
                        
#                         self.sketch.delExternal(len(self.sketch.ExternalGeometry) - 1)
#                         addStringIDExternalGeo(stringId, self.sketch, container)
#         except:
#             self.cleanup()
        

#     # def clearSelection(self, doc):
#         # if self.widget:
#             # self.widget.listWidget.clear()
#             # self.widget.emitSelection()

# class CreateExternalGeo:
#     def GetResources(self):
#         return {
#             'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "PartContainer.svg"),
#             'MenuText': "Create external geometry",
#             'ToolTip': "Creates an external geometry reference in a sketch with persistant naming."
#         }
        
#     def Activated(self):
#         edit = Gui.ActiveDocument.getInEdit()

#         if edit != None:
#             sketch = edit.Object

#             if hasattr(sketch, "TypeId") and sketch.TypeId == "Sketcher::SketchObject":
#                 print("create external geometry")

#                 ExternalGeoSelector(sketch)

#                 Gui.runCommand('Sketcher_CompExternal',0) #jank
#             else:
#                 App.Console.PrintError("You must be editing a sketch!")
                
#     def IsActive(self):
#         return True

# Gui.addCommand('CreateExternalGeo', CreateExternalGeo())