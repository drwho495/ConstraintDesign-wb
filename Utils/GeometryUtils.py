# SPDX-License: LGPL-2.1-or-later

from __future__ import annotations
from Utils.Utils import getP2PDistanceAlongNormal
import Part  # type: ignore
import FreeCAD as App  # type: ignore


# this will eventually have generic boundary generation code
# -- like stuff to make boundaries and points from sections


def getIntersectingFaces(
    prevShape: Part.Shape,
    individualShape: Part.Shape,
    boundaryShape: Part.Shape,
    prevShapeElementMap: dict,
) -> dict:
    """
    Get a list of faces from the previous shape that intersect with the individual shape.
    The faces are sorted by their distance from the sketch center along the normal vector.
    """

    shape2BB = individualShape.BoundBox
    faceMap = getIDsOfFaces(prevShape, boundaryShape, prevShapeElementMap)
    retFaceMap = {}

    intersecting = (
        (faceName, prevShape.getElement(faceName).common(individualShape), identifier)
        for faceName, identifier in faceMap.items()
        if shape2BB.intersect(prevShape.getElement(faceName).BoundBox)
    )

    for faceName, common, identifier in intersecting:
        faceShape = prevShape.getElement(faceName)

        if (not common.isNull() 
            and not common.ShapeType == "Compound"
        ):
            retFaceMap[faceName] = {"Identifier": identifier, "Shape": faceShape}

    return retFaceMap

def getIDsOfFaces(
    shape: Part.Shape,
    boundaryShape: Part.Shape,
    elementMap: dict
) -> dict:
    retMap = {}

    for _, val in elementMap.items():
        mapEdgeArray = val["Element"].split(".")

        if len(mapEdgeArray) == 2 and mapEdgeArray[1].startswith("Edge"):
            mapEdge = boundaryShape.getElement(mapEdgeArray[1])
            for i, face in enumerate(shape.Faces):
                faceName = f"Face{i + 1}"
                for edge in face.Edges:
                        if not faceName in retMap and (hasattr(mapEdge, "Curve") and hasattr(edge, "Curve")) and edge.Curve.isSame(mapEdge.Curve, 1e-2, 1e-2) and "Identifier" in val:
                            retMap[faceName] = val["Identifier"]
    return retMap