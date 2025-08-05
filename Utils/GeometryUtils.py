# SPDX-License: LGPL-2.1-or-later

from __future__ import annotations
from typing import TYPE_CHECKING
from Utils.Utils import getP2PDistanceAlongNormal

if TYPE_CHECKING:
    import Part  # type: ignore
    import FreeCAD as App  # type: ignore


# this will eventually have generic boundary generation code
# -- like stuff to make boundaries and points from sections


def getIntersectingFaces(
    prevShape: Part.Shape,
    individualShape: Part.Shape,
    sketchCenter: App.Vector,
    normal: App.Vector,
) -> list[Part.Face]:
    """
    Get a list of faces from the previous shape that intersect with the individual shape.
    The faces are sorted by their distance from the sketch center along the normal vector.
    """

    shape2BB = individualShape.BoundBox

    intersecting = (
        (face, face.common(individualShape))
        for face in prevShape.Faces
        if shape2BB.intersect(face.BoundBox)
    )

    faces = {
        getP2PDistanceAlongNormal(sketchCenter, face.CenterOfMass, normal): face
        for face, common in intersecting
        if not common.isNull() and not common.ShapeType == "Compound"
    }

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