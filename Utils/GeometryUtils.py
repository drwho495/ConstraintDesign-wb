# SPDX-License: LGPL-2.1-or-later

from __future__ import annotations
from Utils.Utils import addElementToCompoundArray, getElementNameInLists, getElementTypeOfName, getElementNameInShape
import Part  # type: ignore
import FreeCAD as App  # type: ignore
from typing import List, Tuple, Union, Dict
import Utils.Constants as Constants
import time
import re

# ElementMapType: dict[int, dict[str, Union[Part.Shape, str]]]

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


def getDirectionOfLine(
    linePoints: list[App.Vector]
) -> App.Vector: 
    direction = linePoints[1].sub(linePoints[0])
    if direction.Length == 0:
        return App.Vector()
    return abs(direction.normalize())

ancestorCounter = 0
def pointOnCurve(
    curve: Part.Curve,
    vector: App.Vector,
    tolerance: float = 1e-7
):
    try:
        foundParam = curve.parameter(vector)

        return curve.value(foundParam).isEqual(vector, tolerance)
    except Exception as e:
        print(e)
        return False

def getProperCurve(
    edge: Part.Edge
) -> Part.Curve:
    if hasattr(edge, "Curve"):
        retCurve = edge.Curve

        if edge.Curve.TypeId == "Part::GeomLine" and len(edge.Vertexes) >= 2:
            retCurve = Part.LineSegment(edge.Vertexes[0].Point, edge.Vertexes[-1].Point)
        
        return retCurve
    else:
        return None

def doEdgesIntersect(
    edge1: Part.Edge,
    edge2: Part.Edge,
    tolerance: float = 1e-2
) -> bool:
    if hasattr(edge1, "Curve") and hasattr(edge2, "Curve"):
        edge1Curve = getProperCurve(edge1)
        edge2Curve = getProperCurve(edge2)

        edge1Start = edge1Curve.value(edge1Curve.FirstParameter)
        edge2Start = edge2Curve.value(edge2Curve.FirstParameter)

        edge1End = edge1Curve.value(edge1Curve.LastParameter)
        edge2End = edge2Curve.value(edge2Curve.LastParameter)

        if (
            (((edge1Start.isEqual(edge2Start, tolerance) and edge1End.isEqual(edge2End, tolerance))
            or (edge1Start.isEqual(edge2End, tolerance) and edge1End.isEqual(edge2Start, tolerance)))
            or (
                (pointOnCurve(edge1Curve, edge2Start, tolerance) and pointOnCurve(edge1Curve, edge2End, tolerance))
                or (pointOnCurve(edge2Curve, edge1Start, tolerance) and pointOnCurve(edge2Curve, edge1End, tolerance))
            ))
            and (
                pointOnCurve(edge1Curve, edge2Curve.value((edge2Curve.FirstParameter + edge2Curve.LastParameter) / 2), tolerance)
                or pointOnCurve(edge2Curve, edge1Curve.value((edge1Curve.FirstParameter + edge1Curve.LastParameter) / 2), tolerance)
            )
        ):
            return True
    return False

def makeElementMapEntry(identifier, element, elementType):
    return {"Identifier": identifier, "Element": element, "ElementType": elementType}

def makeIdentifier(idType = "A", ids = [], opCode = "XTR", tag = 0, suffix = ""):
    return f"{idType}({','.join(ids)});{opCode}:{tag}{suffix}"

def getIDsString(identifier: str):
        matches = re.findall(r"([A-Za-z])\(([^)]+)\)", identifier)
        mappedIDs = []

        for letter, inside in matches:
            mappedIDs.append((letter, inside.split(",")))
        
        return mappedIDs

def identifierEqual(identifier1: str, identifier2: str) -> bool:
    identifier1GeoIDs = getIDsString(identifier1)
    identifier2GeoIDs = getIDsString(identifier2)

    if len(identifier1GeoIDs) == len(identifier2GeoIDs):
        for i, id1Section in enumerate(identifier1GeoIDs):
            id2Section = identifier2GeoIDs[i]

            occurences = len(set(id1Section[1]) & set(id2Section[1]))
            if occurences < Constants.standardElementSimilarityMinimum or id1Section[0] != id2Section:
                return False
        return True
    else:
        return False


def updateElement(
    elementMap: Dict[int, dict[str, Union[Part.Shape, str]]],
    entry: Dict[str, str],
    elementCounter: int = 0
) -> Tuple[int, int]:
    for elementID, elementEntry in elementMap.copy().items():
        if (elementEntry["ElementType"] == entry["ElementType"]
            and (elementEntry["Identifier"] == entry["Identifier"] 
                 or identifierEqual(elementEntry["Identifier"], entry["Identifier"]))
        ):
            elementMap[elementID] = entry
            return elementID, elementCounter
    
    elementID = elementCounter
    elementMap[elementID] = entry
    elementCounter += 1

    return elementID, elementCounter

def getShapeOfIDList(
    idList: Dict[str, Part.Curve],
    tag = 0
) -> Tuple[Part.Compound, Dict[int, Dict[str, Union[Part.Shape, str]]]]:
    compoundList = []
    edgeList = []
    vertexList = []
    faceList = []
    retDict = {}
    elMapPosition = 0

    for geoID, geom in idList.items():
        geomShape = geom.toShape()

        addElementToCompoundArray(geomShape, compoundList, edgeList, vertexList)
        elementName = getElementNameInLists(geomShape, edgeList, vertexList, faceList)

        if elementName == None:
            print(type(geomShape))
            print(geomShape in edgeList)
            continue

        retDict[elMapPosition] = makeElementMapEntry(geoID, elementName, getElementTypeOfName(elementName))
        elMapPosition += 1

        if isinstance(geomShape, Part.Edge) and hasattr(geom, "StartPoint") and hasattr(geom, "EndPoint"):
            for vert in geomShape.Vertexes:
                subElementName = getElementNameInLists(vert, edgeList, vertexList, faceList)
                if subElementName == None: continue

                if vert.Point.isEqual(geom.StartPoint, 1e-5):
                    retDict[elMapPosition] = makeElementMapEntry(f"{geoID}v1", subElementName, "Vertex")
                    elMapPosition += 1
                elif vert.Point.isEqual(geom.EndPoint, 1e-5):
                    retDict[elMapPosition] = makeElementMapEntry(f"{geoID}v2", subElementName, "Vertex")
                    elMapPosition += 1

    retShape = Part.Compound(compoundList)
    retShape.Tag = tag

    return retShape, retDict

def mapChildShapes(
    shape: Part.Shape,
    childShapes: List[Tuple[Part.Shape, Dict[int, Dict[str, Union[Part.Shape, str]]]]],
    currentMap: Dict[int, Dict[str, Union[Part.Shape, str]]],
    opCode = "SKT",
    mapCounter: int = 0
) -> Tuple[Dict[int, Dict[str, Union[Part.Shape, str]]], int]:
    retMap = currentMap.copy()

    for childShapeEntry in childShapes:
        for _, elMapEntry in childShapeEntry[1].items():
            # we make a custom ID here, since this isn't ancestry based, it's history based
            identifier = makeIdentifier("H", [elMapEntry["Identifier"]], opCode, childShapeEntry[0].Tag)
            childElement = childShapeEntry[0].getElement(elMapEntry["Element"])

            if isinstance(childElement, Part.Edge):
                for i, shEdge in enumerate(shape.Edges):
                    if doEdgesIntersect(childElement, shEdge):
                        _, mapCounter = updateElement(retMap, makeElementMapEntry(identifier, f"Edge{i + 1}", "Edge"), mapCounter)
            if isinstance(childElement, Part.Vertex):
                for i, shVertex in enumerate(shape.Vertexes):
                    if childElement.Point.isEqual(shVertex.Point, 1e-5):
                        _, mapCounter = updateElement(retMap, makeElementMapEntry(identifier, f"Vertex{i + 1}", "Vertex"), mapCounter)

    return retMap, mapCounter

ancestorTime = 0

def getAncestors(
    shape: Part.Shape,
    element: Part.Shape,
) -> Dict[str, List[Part.Shape]]:
    global ancestorTime
    global ancestorCounter
    ancestorCounter += 1
    start = time.time()
    returnDict = {}

    if isinstance(element, Part.Edge) or isinstance(element, Part.Vertex):
        checkVertexes = []
        checkVertexes.extend(element.Vertexes)
        
        for vert in checkVertexes:
            edgeList = shape.ancestorsOfType(vert, Part.Edge)

            if len(edgeList) != 0:
                vertName = getElementNameInShape(vert, shape)

                if vertName not in returnDict:
                    returnDict[vertName] = []
                
                returnDict[vertName].extend(edgeList)

            elementName = getElementNameInShape(element, shape)
            if elementName not in returnDict:
                returnDict[elementName] = []

            returnDict[elementName].extend(shape.ancestorsOfType(vert, Part.Vertex))
    
    ancestorTime += time.time() - start
    return returnDict

def mapAncestors(
    shape: Part.Shape,
    element: Part.Shape,
    ancestryTree: Dict[str, List[str]],
    opCode: str = "",
    lastElementName = ""
):
    global ancestorCounter
    elementName = getElementNameInShape(element, shape)
    ancestors = getAncestors(shape, element)

    for baseName, ancestorList in ancestors.items():
        for ancestor in ancestorList:
            ancestoryElementName = getElementNameInShape(ancestor, shape)

            if ancestoryElementName != None:
                # if ancestoryElementName in ancestryTree:
                    # continue

                if ancestoryElementName not in ancestryTree:
                    ancestryTree[ancestoryElementName] = []
                elif baseName in ancestryTree[ancestoryElementName]:
                    print(f"element: {lastElementName} already in tree")
                    continue

                ancestryTree[ancestoryElementName].append(baseName)
            else:
                print("element name is none!")
            
            print(f"map: {ancestoryElementName}")
            mapAncestors(shape, ancestor, ancestryTree, opCode, ancestoryElementName)
        
def mapFullShape(
    shape: Part.Shape,
    currentMap: Dict[int, Dict[str, Union[Part.Shape, str]]],
    opCode: str = "",
    mapCounter: int = 0
) -> Tuple[Dict[int, Dict[str, Union[Part.Shape, str]]], int]:
    global ancestorCounter
    global ancestorTime

    ancestorCounter = 0
    ancestorTime = 0
    retMap = currentMap.copy()
    ancestryTree = {}

    mapAncestors(shape, shape.getElement(retMap[0]["Element"]), ancestryTree, opCode)
    print(ancestryTree)
    print(ancestorCounter)
    print(ancestorTime)

    elementMapNames = {}
    mappedIndexedNames = []

    for element, ancestorElements in ancestryTree.items():
        if ancestorElements not in mappedIndexedNames:
            mappedIndexedNames.extend(ancestorElements)
        
        if element not in mappedIndexedNames:
            mappedIndexedNames.append(element)

    for elementID, entry in retMap.items():
        idList = getIDsString(entry["Identifier"])
        isHistoryEntry = True

        for section in idList:
            if section[0] != "H":
                isHistoryEntry = False
                break

        if isHistoryEntry:
            elementMapNames[entry["Element"]] = elementID

    mappedTree = False
    currentItem = None
    currentItemIndex = 0
    i = 0

    print(f"elementMapNames: {elementMapNames}\n")
    print(f"mappedIndexedNames: {mappedIndexedNames}\n")
    
    while not mappedTree and i < 50_000:
        i += 1
        if len(mappedIndexedNames) <= currentItemIndex:
            currentItemIndex = 0
            allProperlyMapped = True

            for base, ancestorElements in ancestryTree.items():
                ids = []

                for ancestorElement in ancestorElements:
                    if getElementTypeOfName(ancestorElement) != None:
                        allProperlyMapped = False
                    else:
                        ids.append(ancestorElement)
                
                if len(ids) != 0:
                    newID, mapCounter = updateElement(retMap, makeElementMapEntry(
                        makeIdentifier(
                            "A", 
                            ids, 
                            opCode, 
                            shape.Tag), 
                        base, 
                        getElementTypeOfName(base)
                        ), mapCounter)
                    
                    elementMapNames[base] = newID                    
            
            if allProperlyMapped:
                break
        
        currentItem = mappedIndexedNames[currentItemIndex]
        currentItemIndex += 1
        
        if currentItem in elementMapNames:
            elementID = elementMapNames[currentItem]

            for _, ancestorElements in ancestryTree.items():
                if currentItem in ancestorElements:
                    ancestorElements.remove(currentItem)
                    ancestorElements.append(str(elementID))
    print(ancestryTree)

    return retMap, mapCounter