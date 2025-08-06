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


def isPointOnLine(
    linePoints: list[App.Vector],
    checkPoint: App.Vector, 
    tol=1e-5
) -> bool:
    ab = checkPoint.sub(linePoints[1])
    ap = linePoints[0].sub(linePoints[1])

    if ab.Length == 0:
        return ap.Length <= tol

    cross = ab.cross(ap)
    if cross.Length > tol:
        return False

    # dot_ab_ap = ab.dot(ap)
    # if dot_ab_ap < -tol:
    #     return False
    # if dot_ab_ap > ab.dot(ab) + tol:
    #     return False

    return True

def getDirectionOfLine(
    linePoints: list[App.Vector]
) -> App.Vector: 
    direction = linePoints[1].sub(linePoints[0])
    if direction.Length == 0:
        print("direction failed")
        return App.Vector()
    return abs(direction.normalize())

def doEdgesIntersect(
    edge1: Part.Edge,
    edge2: Part.Edge,
    tolerance: float = 1e-2
) -> bool:
    if len(edge1.Vertexes) >= 2 and len(edge2.Vertexes) >= 2:
        edge1Points = [edge1.Vertexes[0].Point, edge1.Vertexes[-1].Point]
        edge2Points = [edge2.Vertexes[0].Point, edge2.Vertexes[-1].Point]

        if edge1Points[0].isEqual(edge2Points[0], tolerance) and edge1Points[1].isEqual(edge2Points[1], tolerance):
            return True
        elif (
            ((isPointOnLine(edge1Points, edge2Points[0], tolerance) or isPointOnLine(edge1Points, edge2Points[1], tolerance))
            or (isPointOnLine(edge2Points, edge1Points[0], tolerance) or isPointOnLine(edge2Points, edge1Points[1], tolerance)))
            and getDirectionOfLine(edge1Points).isEqual(getDirectionOfLine(edge2Points), .2)
        ):
            return True
    elif (hasattr(edge1, "Curve") and hasattr(edge2, "Curve") 
          and (edge1.Curve.TypeId == "Part::GeomCircle" and edge2.Curve.TypeId == "Part::GeomCircle")
    ):
        if (
            edge1.Curve.Axis.isEqual(edge2.Curve.Axis, tolerance)
            and edge1.Curve.Location.isEqual(edge2.Curve.Location, 1) # needs lower tolerance
            and abs(edge1.Curve.Radius - edge2.Curve.Radius) < tolerance
        ):
            return True
    return False