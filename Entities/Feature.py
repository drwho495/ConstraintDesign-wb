from abc import ABC, abstractmethod
import json
import string
import random
import sys
import os
import FreeCAD as App
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from Entities.Entity import Entity
from Utils import Constants
from Utils import Utils

class Feature(Entity):
    @abstractmethod
    def getBoundaries(self, obj, isShape=False):
        return []

    def getSupports(self, obj):
        return []

    def updateVisibility(self, obj, showObj = False, showBoundary = True):
        obj.Visibility = showObj

        if hasattr(obj, "Boundary") and obj.Boundary != None:
            obj.Boundary.Visibility = showBoundary

    @abstractmethod
    def onChanged(self, obj, prop):
        if prop == "Visibility" and obj.Visibility == True:
            container = self.getContainer(obj)

            if container != None:
                container.Proxy.setShownObj(container, obj)

                if hasattr(obj, "Boundary") and obj.Boundary != None:
                    obj.Boundary.Visibility = True
    
    def getIndividualShapes(self, obj):
        """ Returns a dictionary where {<Index>: {"Shape": shape, "Remove": False}} """
        if hasattr(obj, "Remove"):
            return {0: {"Shape": obj.IndividualShape, "Remove": obj.Remove}}
        else:
            return {0: {"Shape": obj.IndividualShape, "Remove": False}}

    @abstractmethod
    def updateProps(self, obj, hasIndividualShape=True, hasRemove=True):
        if not hasattr(obj, "Suppressed"):
            obj.addProperty("App::PropertyBool", "Suppressed", "ConstraintDesign", "Is feature used.")
            obj.Suppressed = False
        
        if not hasattr(obj, "Remove") and hasRemove:
            obj.addProperty("App::PropertyBool", "Remove", "ConstraintDesign", "Determines the type of boolean operation to perform.")
            obj.Remove = False
        
        if not hasattr(obj, "ElementMap"):
            obj.addProperty("App::PropertyString", "ElementMap", "ConstraintDesign", "The element map of this extrusion.")
            obj.ElementMap = "{}"
        
        if not hasattr(obj, "IndividualShape") and hasIndividualShape:
            obj.addProperty("Part::PropertyPartShape", "IndividualShape", "ConstraintDesign")
            obj.setEditorMode("IndividualShape", 3)


    @abstractmethod
    def getContainer(self, obj):
        return Utils.getParent(obj, "PartContainer")