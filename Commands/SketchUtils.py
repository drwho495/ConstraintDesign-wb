import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui
from Utils import getElementFromHash, getIDsFromSelection, getObjectsFromScope
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."

def positionSketch(sketch, container):
    if hasattr(sketch, "Support") and not hasattr(sketch, "SupportHashes"):
        sketch.addProperty("App::PropertyStringList", "SupportHashes", "Base")
        sketch.SupportHashes = sketch.Support

        sketch.removeProperty("Support")

    if not hasattr(sketch, "SupportPlane"): 
        sketch.addProperty("App::PropertyXLink", "SupportPlane", "Base")
    
    if not hasattr(sketch, "SupportType"): 
        sketch.addProperty("App::PropertyEnumeration", "SupportType", "Base")
        sketch.SupportType = ["Plane", "Hashes"]
        sketch.SupportType = "Hashes"
    
    if hasattr(sketch, "SupportType") and hasattr(sketch, "SupportPlane") and hasattr(sketch, "SupportHashes"):
        if sketch.SupportType == "Hashes":
            vectors = []

            for hash in sketch.SupportHashes:
                boundary, elementName = getElementFromHash(container, hash)
                element = boundary.Shape.getElement(elementName)

                if type(element).__name__ == "Edge":
                    if len(element.Vertexes) == 2:
                        vectors.append(element.Vertexes[0].Point)
                        vectors.append(element.Vertexes[1].Point)
                    else:
                        for vertex in element.Vertexes:
                            vectors.append(vertex.Point)
                elif type(element).__name__ == "Vertex":
                    vectors.append(element.Point)

            if len(vectors) >= 3:
                p1 = vectors[0]
                p2 = vectors[1]
                p3 = vectors[2]

                x_axis = (p2 - p1).normalize()
                normal = (p2 - p1).cross(p3 - p1).normalize()
                y_axis = normal.cross(x_axis)

                rot = FreeCAD.Rotation(x_axis, y_axis, normal)
                translation = p1 - rot.multVec(FreeCAD.Vector(0, 0, 0))

                sketch.Placement = FreeCAD.Placement(translation, rot)
        elif sketch.SupportType == "Plane":
            sketch.Placement = sketch.SupportPlane.Placement

def makeSketch(hashes):
    activeObject = FreeCADGui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")

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
        FreeCAD.Console.PrintError("You need to select a part container as your active object!\n")

class CreateSketch:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "PartContainer.svg"),
            'MenuText': "Create a Sketch",
            'ToolTip': "Creates a new Sketch with a hasher attachement"
        }
        
    def Activated(self):
        selection = FreeCADGui.Selection.getCompleteSelection()
        elements = getIDsFromSelection(selection)

        if FreeCAD.GuiUp == True:
            makeSketch(elements)
        
    def IsActive(self):
        return True

FreeCADGui.addCommand('CreateSketch', CreateSketch())

class CreateExternalGeo:
    def GetResources(self):
        return {
            'Pixmap': os.path.join(os.path.dirname(__file__), "..", "icons", "PartContainer.svg"),
            'MenuText': "Create external geometry",
            'ToolTip': "Creates an external geometry reference in a sketch with persistant naming."
        }
        
    def Activated(self):
        sketch = FreeCADGui.ActiveDocument.getInEdit().Object

        if hasattr(sketch, "TypeId") and sketch.TypeId == "Sketcher::SketchObject":
            pass
        else:
            FreeCAD.Console.PrintError("You must be editing a sketch!")

        
    def IsActive(self):
        return True

FreeCADGui.addCommand('CreateExternalGeo', CreateExternalGeo())