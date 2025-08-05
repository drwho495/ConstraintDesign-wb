import json
import FreeCAD as App
import FreeCADGui as Gui
import random
import string
import Part
from Utils.Constants import *
from Utils.Utils import getP2PDistanceAlongNormal

# this will eventually have generic boundary generation code -- like stuff to make boundaries and points from sections

def getIntersectingFaces(prevShape, individualShape, sketchCenter, normal):
    shape2BB = individualShape.BoundBox
    faces = {}

    for face in prevShape.Faces:
        if not face.BoundBox.intersect(shape2BB):
            continue

        distanceStart = getP2PDistanceAlongNormal(sketchCenter, face.CenterOfMass, normal)

        common = face.common(individualShape)
        if not common.isNull() and not common.ShapeType == "Compound":
            faces[distanceStart] = face

    return list(dict(sorted(faces.items())).values())

def getIDsOfFaces(shape, boundaryShape, elementMap):
    retMap = {}

    for stringID, val in elementMap.items():
        mapEdgeArray = val["Element"].split(".")

        if len(mapEdgeArray) == 2 and mapEdgeArray[1].startswith("Edge"):
            mapEdge = boundaryShape.getElement(mapEdgeArray[1])
            for i, face in enumerate(shape.Faces):
                faceName = f"Face{i + 1}"
                for edge in face.Edges:
                        if not faceName in retMap and (hasattr(mapEdge, "Curve") and hasattr(edge, "Curve")) and edge.Curve.isSame(mapEdge.Curve, 1e-2, 1e-2) and "Identifier" in val:
                            retMap[faceName] = val["Identifier"]
                            # Part.show(face)
                            # print("add to retMap")
                        # else:
                            # print(f"failed: {edge.Curve.isSame(mapEdge.Curve, 1e-2, 1e-2)}")
    # return retMap