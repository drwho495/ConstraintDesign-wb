import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # allow python to see ".."
from SolverSystem.SolvableEntity import SolvableEntity
from SolverSystem.InternalEntities.Plane import Plane

class DatumPlane(SolvableEntity):
    def __init__(self, obj):
        self.internalMovableElements = False
        self.shape = Part.Shape()
        obj.Proxy = self
        
        if not hasattr(obj, "Type"):
            obj.addProperty("App::PropertyString", "Type", "ConstraintDesign", "Type of constraint design feature.")
            obj.Type = "DatumPlane"
        
        if not hasattr(obj, "OriginName"):
            obj.addProperty("App::PropertyString", "OriginName", "ConstraintDesign", "Name of the origin object.")

    def getConstrainedElements(self):
        pass