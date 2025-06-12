import json
import FreeCAD as App
import FreeCADGui as Gui

featureTypes = ["Extrusion", "Fillet", "PartMirror", "Derive"]
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
    
    print(typeLs)

    if hasattr(obj, "InList"):
        for item in obj.InList:
            if hasattr(item, "Type") and item.Type in typeLs and hasattr(item, "Group") and obj in item.Group:
                return item
    
    return None

def getElementFromHash(activeContainer, fullHash, asList = False):
    """
        Get an element (or elements) from a hash or list of hashes

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
                    App.Console.PrintError("Hash: " + str(hash) + " cannot be found in " + feature.Label)
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
            objPartContainer = getParent(feature, "PartContainer")
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
                    print(boundary.Name + "." + elementName)
                    print(value["Element"])

                    if value["Element"] == boundary.Name + "." + elementName:
                        return scopeStart + feature.Name + "." + hash
        else:
            print("no map")

""" Returns None if error """
def getIDsFromSelection(fullSelection):
    elements = []
    hashes = []
    for obj in fullSelection:
        if obj.HasSubObjects:
            elements.append((obj.Object, obj.SubElementNames[0]))

    if len(elements) == 0:
        App.Console.PrintError("You must select at least one element!\n")
        return None
    
    activeObject = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")
    if activeObject != None and isType(activeObject, "PartContainer"):
        for element in elements:
            id = getStringID(activeObject, element, False)

            if id != None:
                hashes.append(id)

        return hashes
    else:
        App.Console.PrintError("You must select a Part Container as an active object!\n")
        return None

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