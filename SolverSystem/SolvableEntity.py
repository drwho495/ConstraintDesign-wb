from abc import ABC, abstractmethod

class SolvableEntity(ABC):
    @abstractmethod
    def __init__(self):
        self.internalMovableElements = False

    def hasInternalMovableElements(self):
        return self.internalMovableElements

    # @abstractmethod
    # def generateEquations(self):
        # pass

    # @abstractmethod
    # def generateParameters(self):
        # pass

    @abstractmethod
    def getConstrainedElements(self):
        pass