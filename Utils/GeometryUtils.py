# SPDX-License: LGPL-2.1-or-later

from __future__ import annotations
from Utils import Utils
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
            retFaceMap[faceName] = {"Identifier": "|".join(identifier), "Shape": faceShape}

    return retFaceMap

def getIDsOfFaces(
    shape: Part.Shape,
    boundaryShape: Part.Shape,
    elementMap: dict
) -> dict:
    retMap = {}

    for _, val in elementMap.items():
        mapEdgeArray = val["Element"].split(".")

        if len(mapEdgeArray) == 2 and mapEdgeArray[1].startswith("Edge") and (not hasattr(val, "Stale") or not val["Stale"]):
            numb = int(mapEdgeArray[1][4:])

            if len(boundaryShape.Edges) >= numb:
                mapEdge = boundaryShape.getElement(mapEdgeArray[1])
                for i, face in enumerate(shape.Faces):
                    faceName = f"Face{i + 1}"
                    for edge in face.Edges:
                        if doEdgesIntersect(mapEdge, edge) and "Identifier" in val:
                            identifier = val["Identifier"].rstrip(';')

                            if not faceName in retMap:
                                retMap[faceName] = []
                            
                            if identifier not in retMap[faceName]:
                                retMap[faceName].append(identifier)
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
        return App.Vector()
    return abs(direction.normalize())

def pointOnCurve(
    curve: Part.Curve,
    vector: App.Vector
):
    try:
        foundParam = curve.parameter(vector)

        return curve.value(foundParam).isEqual(vector, 1e-7)
    except:
        return False

def doEdgesIntersect(
    edge1: Part.Edge,
    edge2: Part.Edge,
    tolerance: float = 1e-2
) -> bool:
    try:
        hasattr(edge1, "Curve")
        hasattr(edge2, "Curve")
    except:
        # undefined curve type
        print("undefined curve type!")
        return False

    if hasattr(edge1, "Curve") and hasattr(edge2, "Curve"):
        edge1Curve: Part.Curve = edge1.Curve
        edge2Curve: Part.Curve = edge2.Curve

        if edge1Curve.TypeId == "Part::GeomLine":
            edge1Curve = Part.LineSegment(edge1.Vertexes[0].Point, edge1.Vertexes[-1].Point)
        
        if edge2Curve.TypeId == "Part::GeomLine":
            edge2Curve = Part.LineSegment(edge2.Vertexes[0].Point, edge2.Vertexes[-1].Point)

        edge1Start = edge1Curve.value(edge1Curve.FirstParameter)
        edge2Start = edge2Curve.value(edge2Curve.FirstParameter)

        edge1End = edge1Curve.value(edge1Curve.LastParameter)
        edge2End = edge2Curve.value(edge2Curve.LastParameter)

        if (
            (((edge1Start.isEqual(edge2Start, tolerance) and edge1End.isEqual(edge2End, tolerance))
            or (edge1Start.isEqual(edge2End, tolerance) and edge1End.isEqual(edge2Start, tolerance)))
            or (
                (pointOnCurve(edge1Curve, edge2Start) and pointOnCurve(edge1Curve, edge2End))
                or (pointOnCurve(edge2Curve, edge1Start) and pointOnCurve(edge2Curve, edge1End))
            ))
            and (
                pointOnCurve(edge1Curve, edge2Curve.value((edge2Curve.FirstParameter + edge2Curve.LastParameter) / 2))
                or pointOnCurve(edge2Curve, edge1Curve.value((edge1Curve.FirstParameter + edge1Curve.LastParameter) / 2))
            )
        ):
            return True
    return False