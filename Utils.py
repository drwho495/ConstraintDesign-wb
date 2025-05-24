acceptableFeatureTypes = ["Extrusion", "Fillet", "PartMirror"]
nonFeatureEntityTypes = ["ExposedGeometry"]
datumNames = ["WiresDatum", "SketchProjection"]

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