from abc import ABC, abstractmethod
import json
import string
import random
import sys
import os
import FreeCAD as App
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from Utils import Utils

class Entity(ABC):
    @abstractmethod
    def __init__(self):
        pass

    def markModified(self, obj, mark = True):
        if hasattr(obj, "Modified"):
            obj.Modified = mark

    @abstractmethod
    def updateProps(self, obj, hasModified = False):
        if not hasattr(obj, "Modified") and hasModified:
            obj.addProperty("App::PropertyBool", "Modified", "ConstraintDesign")
            obj.setEditorMode("Modified", 3)
            obj.Modified = True

    def getContainer(self, obj):
        return Utils.getParent(obj, "PartContainer")