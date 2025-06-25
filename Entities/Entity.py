from abc import ABC, abstractmethod
import json
import string
import random
import sys
import os
import FreeCAD as App
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from Utils import getParent

class Entity(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def getBoundaries(self, obj, isShape=False):
        return []

    def generateHashName(self, map):
        keys = map.keys()
        newHash = ""

        while True:
            newHash = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

            if newHash not in keys:
                break
        
        return newHash

    @abstractmethod
    def updateProps(self, obj):
        pass

    @abstractmethod
    def onChanged(self, obj, prop):
        if prop == "Visibility" and obj.Visibility == True:
            container = self.getContainer(obj)

            if container != None:
                container.Proxy.setShownObj(container, obj)
            else:
                App.Console.PrintWarning("No container found in onChanged!")

    @abstractmethod
    def getContainer(self, obj):
        return getParent(obj, "PartContainer")