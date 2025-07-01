from abc import ABC, abstractmethod
import json
import string
import random
import sys
import os
import FreeCAD as App
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from Utils.Utils import getParent

class Entity(ABC):
    @abstractmethod
    def __init__(self):
        pass

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

    def getContainer(self, obj):
        return getParent(obj, "PartContainer")