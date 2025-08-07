import FreeCAD as App
import FreeCADGui as Gui
import Utils as Utils
from typing import Tuple
import os

# key format:
# <END OF FILENAME>_<PART CONTAINER NAME>
# e.g: Doc2.FCStd_PartContainer002

cachedDocuments = {}

def getCacheDocument(
    partContainer: App.DocumentObject,
    variantLinkObj: App.DocumentObject
) -> Tuple[App.Document, App.DocumentObject]:
    keyName = f"{os.path.split(variantLinkObj.Document.FileName)[1]}_{variantLinkObj.Name}__{os.path.split(partContainer.Document.FileName)[1]}_{partContainer.Name}"
    cacheDoc = None
    docObj = None

    if not keyName in cachedDocuments:
        cacheDoc = App.newDocument(f"{keyName}--cache_doc", hidden = True, temp = True)
        cachedDocuments[keyName] = {"Document": cacheDoc, "Container": None}
    else:
        cacheDoc = cachedDocuments[keyName]["Document"]
        docObj = cachedDocuments[keyName]["Container"]
    
    return cacheDoc, docObj

def getPartContainer(
    document: App.Document
) -> App.DocumentObject:
    for _, info in cachedDocuments.items():
        if info["Document"].Name == document.Name:
            return info["Container"]
    
def setPartContainer(
    document: App.Document,
    container: App.DocumentObject
) -> App.DocumentObject:
    keyVal = {}
    reqKey = ""

    for key, info in cachedDocuments.items():
        if info["Document"].Name == document.Name:
            keyVal = info
            reqKey = key
            break
    
    document = keyVal["Document"]

    for obj in document.Objects:
        document.removeObject(obj.Name)

    keyVal["Container"] = document.copyObject(container, True)
    cachedDocuments[reqKey] = keyVal

    return keyVal["Container"]