import FreeCAD as App
import FreeCADGui as Gui
from Utils import Utils
from typing import Tuple
import os

# key format:
# <END OF FILENAME>_<PART CONTAINER NAME>
# e.g: Doc2.FCStd_PartContainer002

cachedDocuments = {}

def makeKey(
    partContainer: App.DocumentObject,
    variantLinkObj: App.DocumentObject
):
    return f"{os.path.split(variantLinkObj.Document.FileName)[1]}_{variantLinkObj.Name}__{os.path.split(partContainer.Document.FileName)[1]}_{partContainer.Name}"

def deleteCacheDocument(
    partContainer: App.DocumentObject,
    variantLinkObj: App.DocumentObject
):
    keyName = makeKey(partContainer, variantLinkObj)

    if keyName in cachedDocuments:
        document = cachedDocuments[keyName]["Document"]
        App.closeDocument(document.Name)

        cachedDocuments.pop(keyName)

def getCacheDocumentAndContainer(
    partContainer: App.DocumentObject,
    variantLinkObj: App.DocumentObject
) -> Tuple[App.Document, App.DocumentObject]:
    keyName = makeKey(partContainer, variantLinkObj)
    cacheDoc = None
    docObj = None

    if not keyName in cachedDocuments:
        cacheDoc = App.newDocument(f"{keyName}--cache_doc", hidden = True, temp = True)
        cachedDocuments[keyName] = {"Document": cacheDoc, "Container": None}
    else:
        cacheDoc = cachedDocuments[keyName]["Document"]
        docObj = cacheDoc.getObject(cachedDocuments[keyName]["Container"])
    
    return cacheDoc, docObj

def getPartContainer(
    document: App.Document
) -> App.DocumentObject:
    for _, info in cachedDocuments.items():
        if info["Document"].Name == document.Name:
            return info["Document"].getObject(info["Container"])
    
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

    copiedContainer = document.copyObject(container, True)
    keyVal["Container"] = copiedContainer.Name
    cachedDocuments[reqKey] = keyVal

    return copiedContainer