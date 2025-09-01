import json
import FreeCAD as App
import FreeCADGui as Gui
import random
import string
import Part
import importlib
from Utils import Constants

# will add many more test cases; this is only used in one area as of right now (will be used more later)
def getDependencies(obj, activeContainer):
    if isType(obj, "ExposedGeometry"):
        _, _, feature, _ = getObjectsFromScope(activeContainer, obj.Support)

        return [feature.Name]
    else:
        return []

def isGearsWBPart(obj):
    return hasattr(obj, "version") and (hasattr(obj, "num_teeth") or hasattr(obj, "numpoints"))

def fixGear(gear, container = None, addExtrusion = False):
    if container == None:
        container = getParent(gear, "PartContainer")
    
    if not hasattr(gear, "Type"):
        gear.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
        gear.Type = "GearsWBPart"
    
    if addExtrusion and hasattr(gear, "height") and gear.height != 0:
        Extrusion = importlib.import_module("Entities.Extrusion") # do this to avoid circular import

        oldHeight = gear.height.Value
        gear.height = 0
        gear.recompute()

        extrusion = Extrusion.makeExtrusion(container, gear, False)

        if extrusion != None:
            extrusion.recompute()

            if hasattr(extrusion, "Length"):
                extrusion.Length = oldHeight

            container.recompute(True)

def getVariablesOfVariableContainer(container: App.DocumentObject) -> dict:
    propertyDict = {}

    for prop in container.PropertiesList:
        if prop not in Constants.variableContainerDefaultProps:
            propertyDict[prop] = {
                "Type": container.getTypeIdOfProperty(prop),
                "Value": getattr(container, prop)
            }
    return propertyDict

def getDocumentByFileName(fileName):
    for _, document in App.listDocuments().items():
        if document.FileName == fileName:
            return document
    
    oldDocName = App.ActiveDocument.Name
    retDocument = App.openDocument(fileName)
    App.setActiveDocument(oldDocName)

    return retDocument

def isType(obj, typeObj):
    if type(typeObj) == str:
        typeObj = [typeObj]

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

def getP2PDistanceAlongNormal(startPoint, endPoint, normal):
    vec = endPoint - startPoint
    return vec.dot(normal)

def getDistanceToElement(feature, stringID, startPoint, normal, requestingObjectLabel=""):
    boundary, elementName = getElementFromHash(feature, stringID, requestingObjectLabel=requestingObjectLabel)
    element = boundary.Shape.getElement(elementName)

    entityPoint = None

    if isinstance(element, Part.Vertex):
        entityPoint = element.Point
    else:
        entityPoint = element.CenterOfMass

    return getP2PDistanceAlongNormal(startPoint, entityPoint, normal)

def getElementFromHash(activeContainer, fullHash, requestingObjectLabel = "", printMissingError = True, asList = False):
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

        if hasattr(feature, "Proxy") and isType(feature, Constants.featureTypes):
            if hasattr(feature, "ElementMap"):
                map = json.loads(feature.ElementMap)

                if hashName in map and (map[hashName].get("Stale") == None or map[hashName]["Stale"] == False):
                    element = map[hashName]["Element"]
                    elementArray = element.split(".")

                    boundaryName = elementArray[0]
                    elementName = elementArray[1]
                    boundary = feature.Document.getObject(boundaryName)
                    
                    elements.append((boundary, elementName))
                else:
                    if printMissingError:
                        if requestingObjectLabel != "":
                            App.Console.PrintError(f"{requestingObjectLabel}: {str(fullHash)} cannot be found\n")
                        else:
                            App.Console.PrintError(f"{str(fullHash)} cannot be found\n")
            else:
                App.Console.PrintError("Feature has no ElementMap!\nPlease report this!\n")
    
    if asList:
        return elements
    else:
        if len(elements) != 0:
            return elements[0]
        else:
            return None, None   

def getStringID(activeContainer, element, fullScope=False, suppressErrors = False):
        """
            This returns the string ID of an element, with context of the scope in which the element resides.
            Returns a string if successful, returns `None` if not.

            `element` is the element to find. It needs to be formatted like this: (baseObject, elementName)
            `fullScope` makes it so that the full scope is returned with the string ID base
            `suppressErrors` disables error printing in the FreeCAD Console.

            full string ID format: documentName.partContainerName.featureName.stringIDBase
        """
        boundary = element[0]
        elementName = element[1]
        scopeStart = ""
        feature = None

        if isType(boundary, Constants.boundaryTypes):
            feature = getParent(boundary, Constants.featureTypes)
        elif isType(boundary, Constants.featureTypes):
            feature = boundary
        elif isType(boundary, "ExposedGeometry"):
            if hasattr(boundary, "Support"):
                exposedGeoContainer = getParent(boundary, "PartContainer")
                supportDocument, supportContainer, supportFeature, supportID = getObjectsFromScope(exposedGeoContainer, boundary.Support)
                scopeStart = ""

                sameDocument = supportDocument.Name == activeContainer.Document.Name
                sameParent = activeContainer.Name == supportContainer.Name

                if not sameDocument and supportContainer != None and supportContainer != None or fullScope:
                    scopeStart = supportFeature.Document.Name + "." + supportContainer.Name + "."
                
                if not sameParent and sameDocument:
                    scopeStart = supportContainer.Name + "."

                return scopeStart + f"{supportFeature.Name}.{supportID}"
            
        if feature != None:
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
                    if not suppressErrors:
                        App.Console.PrintError("Unable to load json from ElementMap of " + feature.Label)

                if map != None:
                    for hash, value in map.items():
                        if value["Element"] == boundary.Name + "." + elementName and (map[hash].get("Stale") == None or map[hash]["Stale"] == False):
                            return scopeStart + feature.Name + "." + hash
                else:
                    return None

def generateHashName(map):
        keys = map.keys()
        newHash = ""

        while True:
            newHash = ''.join(random.choices(string.ascii_letters + string.digits, k = Constants.hashSize))

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

    if hasattr(activeContainer, "LinkedObject"):
        activeContainer = activeContainer.LinkedObject

    if scopeLen == 4:
        document = App.getDocument(scopeArray[0])
        container = document.getObject(scopeArray[1])
        feature = document.getObject(scopeArray[2])
    elif scopeLen == 3:
        document = activeContainer.Document
        container = document.getObject(scopeArray[0])
        feature = document.getObject(scopeArray[1])
    elif scopeLen == 2:
        document = activeContainer.Document
        container = activeContainer
        feature = document.getObject(scopeArray[0])
    
    elementName = scopeArray[scopeLen - 1]

    return document, container, feature, elementName

def getPlaneFromStringIDList(container, stringList, requestingObjectLabel="", asFace = False):
    elements = getElementFromHash(container, stringList, asList=True, requestingObjectLabel=requestingObjectLabel)

    vectors = []

    if len(elements) == 1:
        boundary = elements[0][0]
        elementName = elements[0][1]
        element = boundary.Shape.getElement(elementName)
        face = Part.makeFace(Part.Wire(element))
        
        if hasattr(element, "Curve") and element.Curve.TypeId == "Part::GeomCircle":
            if not asFace:
                return face.Surface
            else:
                return face

    for element in elements:
        boundary = element[0]
        elementName = element[1]

        if boundary == None or elementName == None: continue

        element = boundary.Shape.getElement(elementName)

        if type(element).__name__ == "Edge":
            for vertex in element.Vertexes:
                pt = vertex.Point

                if pt not in vectors:
                    vectors.append(pt)
        elif type(element).__name__ == "Vertex":
            vectors.append(element.Point)
    
    if len(vectors) >= 3:
        try:
            face = Part.Face(Part.Wire(Part.makePolygon(vectors)))

            if not asFace:
                return face.Surface
            else:
                return face
        except Exception as e:
            App.Console.PrintError(f"{requestingObjectLabel}: unable to create a plane from a list of string IDs!\nThe points created by each element are likely colinear (which means they create a straight line)!\n")
            return None
    else:
        App.Console.PrintError(f"{requestingObjectLabel}: unable to create a plane from a list of string IDs!\nList contents: {','.join(stringList)}\n")
        return None
    
def addElementToCompoundArray(element, compoundList, edgesList, vertexList):
    edgesList.extend(element.Edges)
    vertexList.extend(element.Vertexes)

    compoundList.append(element) 

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
        if not ((hasattr(item, "TypeId") and item.TypeId == "Sketcher::SketchObject") or isType(item, "BoundarySketch")):
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
                    
                    edgeIndex += len(boundary.Shape.Edges)
                    vertexIndex += len(boundary.Shape.Vertexes)
        edgeIndex += newEdgeNum
        vertexIndex += newVertexNum

    
    if generateElementMap:
        return Part.makeCompound(boundaryArray), elementMap
    else:
        return Part.makeCompound(boundaryArray)