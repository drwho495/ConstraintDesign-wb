import os
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui

def positionSketch(sketch, container):
    if hasattr(sketch, "Support"):
        support = sketch.Support
        vectors = []

        for hash in support:
            object, elementName = container.Proxy.getElement(container, hash)
            element = object.Shape.getElement(elementName)

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
            y_axis = normal.cross(x_axis)  # ensures right-handed coordinate system

            rot = FreeCAD.Rotation(x_axis, y_axis, normal)
            translation = p1 - rot.multVec(FreeCAD.Vector(0, 0, 0))

            sketch.Placement = FreeCAD.Placement(translation, rot)

def makeSketch(elements):
    activeObject = FreeCADGui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")

    if activeObject is not None and hasattr(activeObject, "Type") and activeObject.Type == "PartContainer":
        hashes = []

        for element in elements:
            print(element)

            hashes.append(activeObject.Proxy.getHash(activeObject, element, True))
        
        newSketch = activeObject.Document.addObject("Sketcher::SketchObject", "Sketch")
        activeObject.Proxy.addObject(activeObject, newSketch)

        newSketch.setEditorMode("AttacherEngine", 3)
        newSketch.setEditorMode("AttachmentSupport", 3)
        newSketch.setEditorMode("MapMode", 3)

        newSketch.addProperty("App::PropertyStringList", "Support", "Base")
        newSketch.Support = hashes

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
        doc = FreeCAD.ActiveDocument
        if not doc:
            doc = FreeCAD.newDocument()
        
        selection = FreeCADGui.Selection.getCompleteSelection()
        elements = []
        for obj in selection:
            if obj.HasSubObjects:
                elements.append((obj.Object, obj.SubElementNames[0]))

        if len(elements) == 0:
            FreeCAD.Console.PrintError("You must select at least one edge!\n")
            return
        
        # Only works if the gui is up
        if FreeCAD.GuiUp == True:
            makeSketch(elements)
            
        doc.recompute()
        
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