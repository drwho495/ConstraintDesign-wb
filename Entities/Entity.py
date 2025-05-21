from abc import ABC, abstractmethod
import json
import string
import random

class SolvableEntity(ABC):
    @abstractmethod
    def __init__(self):
        pass

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
    def getElement(self, obj, hash):
        pass
    
    @abstractmethod
    def getContainer(self, obj):
        if len(obj.InList) == 0:
            return None
        
        container = obj.InList[0]

        if hasattr(container, "Type") and container.Type == "PartContainer":
            return container
        else:
            return None