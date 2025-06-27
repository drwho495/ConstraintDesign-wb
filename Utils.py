import json
import FreeCAD as App
import FreeCADGui as Gui
import random
import string
import Part

featureTypes = ["Extrusion", "Fillet", "Countersink", "Chamfer", "PartMirror", "Derive", "LinearPattern", "CircularPattern"]
dressupTypes = ["Fillet", "Countersink", "Chamfer"]
datumTypes = ["ExposedGeometry"]
boundaryTypes = ["WiresDatum", "SketchProjection", "Boundary"]

def isType(obj, typeObj):
    if type(typeObj) == str:
        return obj != None and hasattr(obj, "Type") and obj.Type == typeObj
    elif type(typeObj) == list:
        return obj != None and hasattr(obj, "Type") and obj.Type in typeObj

def getParent(obj, parentType):
    typeLs = []
    if type(parentType) == str:
        typeLs = [parentType]
    elif type(parentType) == list:
        typeLs = parentType
    
    if hasattr(obj, "InList"):
        for item in obj.InList:
            if hasattr(item, "Type") and item.Type in typeLs and hasattr(item, "Group") and obj in item.Group:
                return item
    
    return None

def getDistanceToEntity(feature, stringID, startPoint, normal):
    boundary, elementName = getElementFromHash(feature, stringID)
    element = boundary.Shape.getElement(elementName)

    entityPoint = None

    if isinstance(element, Part.Vertex):
        entityPoint = element.Point
    else:
        entityPoint = element.CenterOfMass

    vec = entityPoint - startPoint

    return vec.dot(normal)

def getElementFromHash(activeContainer, fullHash, asList = False):
    """
        Get an element (or elements) from a hash or list of hashes

        The returned element is formatted as `(boundaryObject, elementName)`

        `activeContainer` is necessary in order to determine the right place to look for the element.
        Change `asList` to True to pass a list of hashes, and have a list of elements returned.
    """
    hashesList = []
    elements = []

    if asList:
        if type(fullHash) == list:
            hashesList = fullHash
        else:
            App.Console.PrintError("Passed single hash instead of list!\nReport this as an issue on GitHub please!\n")
    else:
        if type(fullHash) == str:
            hashesList = [fullHash]
        else:
            App.Console.PrintError(f"Passed {type(fullHash).__str__()} instead of string!\nReport this as an issue on GitHub please!\n")

    for hash in hashesList:
        _, _, feature, hashName = getObjectsFromScope(activeContainer, hash)

        if hasattr(feature, "Proxy") and isType(feature, featureTypes):
            if hasattr(feature, "ElementMap"):
                map = json.loads(feature.ElementMap)

                if hashName in map:
                    element = map[hashName]["Element"]
                    elementArray = element.split(".")

                    boundaryName = elementArray[0]
                    elementName = elementArray[1]
                    boundary = feature.Document.getObject(boundaryName)
                    
                    elements.append((boundary, elementName))
                else:
                    App.Console.PrintError(f"Hash: {str(hash)} cannot be found in {feature.Label}\n")
            else:
                App.Console.PrintError("Feature has no ElementMap!\nPlease report this!\n")
    
    if asList:
        return elements
    else:
        if len(elements) != 0:
            return elements[0]
        else:
            return None    

def getStringID(activeContainer, element, fullScope=False):
        boundary = element[0]
        elementName = element[1]
        scopeStart = ""

        if isType(boundary, boundaryTypes):
            feature = getParent(boundary, featureTypes)
        elif isType(boundary, featureTypes):
            feature = boundary
        
        featurePartContainer = getParent(feature, "PartContainer")

        if not isType(activeContainer, "PartContainer"):
            objPartContainer = featurePartContainer
        else:
            objPartContainer = activeContainer

        sameDocument = feature.Document.Name == activeContainer.Document.Name
        if featurePartContainer != None and objPartContainer != None:
            sameParent = objPartContainer.Name == featurePartContainer.Name
        else:
            sameParent = True

        if not sameDocument and featurePartContainer != None and objPartContainer != None or fullScope:
            scopeStart = feature.Document.Name + "." + featurePartContainer.Name + "."
        
        if not sameParent and sameDocument:
            scopeStart = featurePartContainer.Name + "."

        if hasattr(feature, "ElementMap"):
            try:
                map = json.loads(feature.ElementMap)
            except:
                map = None
                App.Console.PrintError("Unable to load json from ElementMap of " + feature.Label)

            if map != None:
                for hash, value in map.items():
                    if value["Element"] == boundary.Name + "." + elementName:
                        return scopeStart + feature.Name + "." + hash

def generateHashName(map):
        keys = map.keys()
        newHash = ""

        while True:
            newHash = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

            if newHash not in keys:
                break
        
        return newHash

def getIDsFromSelection(fullSelection, activeContainer=None):
    elements = []
    hashes = []
    for obj in fullSelection:
        if obj.HasSubObjects and obj.SubElementNames[0] != '':
            elements.append((obj.Object, obj.SubElementNames[0]))

    if len(elements) == 0 or len(fullSelection) == 0:
        return []
    
    if activeContainer == None:
        activeContainer = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")
        
    if activeContainer != None and isType(activeContainer, "PartContainer"):
        for element in elements:
            id = getStringID(activeContainer, element, False)

            if id != None:
                hashes.append(id)
        return hashes
    else:
        App.Console.PrintError("You must select a Part Container as an active object!\n")
        return []

def getObjectsFromScope(activeContainer, hashName):
    document = None
    container = None
    feature = None
    elementName = None
    scopeArray = hashName.split(".")
    scopeLen = len(scopeArray)

    if scopeLen == 4:
        document = App.getDocument(scopeArray[0])
        container = document.getObject(scopeArray[1])
        feature = document.getObject(scopeArray[2])
    elif scopeLen == 3:
        document = App.ActiveDocument
        container = document.getObject(scopeArray[0])
        feature = document.getObject(scopeArray[1])
    elif scopeLen == 2:
        document = App.ActiveDocument
        container = activeContainer
        feature = document.getObject(scopeArray[0])
    
    elementName = scopeArray[scopeLen - 1]

    return document, container, feature, elementName

def makeBoundaryCompound(features, generateElementMap=False, boundaryName = ""):
    """
        This method makes a Part.Compound out of all of all the selected boundaries

        `features` sets which to find the necessary boundaries to compound
        `generateElementMap` creates (and returns) and elementMap with the boundaries
        `boundaryName` is necessary to generate an element map, it is the name of the boundary in which this compound will be set to
    """

    boundaryArray = []
    elementMap = {}
    newEdgeNum = 0
    newVertexNum = 0
    edgeIndex = 0
    vertexIndex = 0

    for item in features:
        if not (hasattr(item, "TypeId") and item.TypeId == "Sketcher::SketchObject"):
            boundaries = []

            if generateElementMap:
                boundaries = item.Proxy.getBoundaries(item, False)
            else:
                boundaries = item.Proxy.getBoundaries(item, True)

            if generateElementMap and boundaryName != "" and hasattr(item, "ElementMap"):
                itemElementMap = json.loads(item.ElementMap)
                
                for boundary in boundaries:
                    boundaryArray.append(boundary.Shape)
                
                    for hash, value in itemElementMap.items():
                        elementArray = value["Element"].split(".")
                        featureName = elementArray[0]
                        elementName = elementArray[1]

                        if featureName == boundary.Name:
                            if elementName.startswith("Edge"):
                                elementNum = int(elementName[4:])
                                elementNum += edgeIndex
                                elementName = "Edge" + str(elementNum)
                            elif elementName.startswith("Vertex"):
                                elementNum = int(elementName[6:])
                                elementNum += vertexIndex
                                elementName = "Vertex" + str(elementNum)

                            value["Element"] = boundaryName + "." + elementName
                            elementMap[hash] = value
                    
                    edgeIndex += len(boundary.Shape.Edges) + 0
                    vertexIndex += len(boundary.Shape.Vertexes) + 0
            # print(elementMap)        
        else: 
            print(item.Label)
            # boundaryArray.extend(boundaries)
        
        print("edge index: " + str(edgeIndex))
        print("vertex index: " + str(vertexIndex))

        edgeIndex += newEdgeNum
        vertexIndex += newVertexNum

    
    print("array: " + str(boundaryArray))
    
    if generateElementMap:
        return Part.Compound(boundaryArray), elementMap
    else:
        return Part.Compound(boundaryArray)